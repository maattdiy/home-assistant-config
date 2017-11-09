"""
Demo fan platform that has a fake fan.

For more details about this platform, please refer to the documentation
https://home-assistant.io/components/demo/
"""
import logging
import asyncio
import threading
import voluptuous as vol
import binascii
import os.path
import socket
import homeassistant.helpers.config_validation as cv
from homeassistant.components.fan import (SPEED_LOW, SPEED_MEDIUM, SPEED_HIGH,
                                          FanEntity, SUPPORT_SET_SPEED,
                                          SUPPORT_OSCILLATE, SUPPORT_DIRECTION, PLATFORM_SCHEMA)
from homeassistant.const import (STATE_OFF, CONF_NAME, CONF_HOST, CONF_MAC, CONF_TIMEOUT, CONF_CUSTOMIZE)
from configparser import ConfigParser
from base64 import b64encode, b64decode

LIMITED_SUPPORT = SUPPORT_SET_SPEED
SUPPORT_SPEED_AND_DIRECTION = SUPPORT_SET_SPEED | SUPPORT_DIRECTION


_LOGGER = logging.getLogger(__name__)

CONF_RFCODES_INI = 'rfcodes_ini'
CONF_SPEEDS = 'speeds'
CONF_DEFAULT_SPEED = 'default_speed'
CONF_DEFAULT_DIRECTION = 'default_direction'
DIRECTION_ANTICLOCKWISE = 'left' #forward
DIRECTION_CLOCKWISE = 'right' #reverse

DEFAULT_NAME = 'Broadlink Fan'
DEFAULT_TIMEOUT = 10
DEFAULT_RETRY = 3
DEFAULT_SPEED_LIST = [STATE_OFF, SPEED_LOW, SPEED_MEDIUM, SPEED_HIGH]
DEFAULT_SPEED = SPEED_MEDIUM
DEFAULT_DIRECTION = DIRECTION_ANTICLOCKWISE

CUSTOMIZE_SCHEMA = vol.Schema({
    vol.Optional(CONF_SPEEDS): vol.All(cv.ensure_list, [cv.string])
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_MAC): cv.string,
    vol.Required(CONF_RFCODES_INI): cv.string,
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
    vol.Optional(CONF_CUSTOMIZE, default={}): CUSTOMIZE_SCHEMA,
    vol.Optional(CONF_DEFAULT_SPEED, default=DEFAULT_SPEED): cv.string,
    vol.Optional(CONF_DEFAULT_DIRECTION, default=DEFAULT_DIRECTION): cv.string
})

# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices_callback, discovery_info=None):
    """Set up the Broadlink-controlled fan platform."""
    name = config.get(CONF_NAME)
    ip_addr = config.get(CONF_HOST)
    mac_addr = binascii.unhexlify(config.get(CONF_MAC).encode().replace(b':', b''))
    speed_list = config.get(CONF_CUSTOMIZE).get(CONF_SPEEDS, []) or DEFAULT_SPEED_LIST
    if not STATE_OFF in speed_list:
        speed_list.insert(0, STATE_OFF)
    default_speed = config.get(CONF_DEFAULT_SPEED)
    default_direction = config.get(CONF_DEFAULT_DIRECTION)
    
    import broadlink
    
    broadlink_device = broadlink.rm((ip_addr, 80), mac_addr)
    broadlink_device.timeout = config.get(CONF_TIMEOUT)

    try:
        broadlink_device.auth()
    except socket.timeout:
        _LOGGER.error("Failed to connect to Broadlink RM Device")
    
    rfcodes_ini_file = config.get(CONF_RFCODES_INI)
    
    if rfcodes_ini_file.startswith("/"):
        rfcodes_ini_file = rfcodes_ini_file[1:]
        
    rfcodes_ini_path = hass.config.path(rfcodes_ini_file)
    
    if os.path.exists(rfcodes_ini_path):
        rfcodes_ini = ConfigParser()
        rfcodes_ini.read(rfcodes_ini_path)
    else:
        _LOGGER.error("The ini file was not found. (" + rfcodes_ini_path + ")")
        return
    
    
    if DIRECTION_ANTICLOCKWISE in rfcodes_ini.sections() and DIRECTION_CLOCKWISE in rfcodes_ini.sections():
        supported_features = SUPPORT_SPEED_AND_DIRECTION
    else:
        supported_features = LIMITED_SUPPORT
    #if 'oscillate' in rfcodes_ini.sections():
    #    supported_features = supported_features | SUPPORT_OSCILLATE
    
    add_devices_callback([
        BroadlinkFan(hass, name, broadlink_device, rfcodes_ini, speed_list, default_speed, default_direction, supported_features)
    ])


class BroadlinkFan(FanEntity):
    """A demonstration fan component."""

    def __init__(self, hass, name: str, broadlink_device, rfcodes_ini, speed_list, default_speed, default_direction, supported_features: int) -> None:
        """Initialize the entity."""
        self.hass = hass
        self._supported_features = supported_features
        self._speed = STATE_OFF
        self.oscillating = None
        self.direction = None
        self._name = name
        self._speed_list = speed_list
        self._default_speed = default_speed

        if supported_features & SUPPORT_OSCILLATE:
            self.oscillating = False
        if supported_features & SUPPORT_DIRECTION:
            self.direction = default_direction
            
        self._broadlink_device = broadlink_device
        self._commands_ini = rfcodes_ini
        
    timer = None
    
    @asyncio.coroutine
    def async_send_ir_after_delay(self):
        if self.timer is not None:
            if self.timer.is_alive():
                self.timer.cancel()
        self.timer = threading.Timer(0.1, self.send_ir)
        self.timer.start()
        
    def send_ir(self): 

        if self._speed == STATE_OFF:
            section = 'off'
            value = 'off_command'
        else:
            if self.direction is None:
                section = DIRECTION_ANTICLOCKWISE
            elif self.direction.lower() == 'left':
                section = DIRECTION_ANTICLOCKWISE
            elif self.direction.lower() == 'right':
                section = DIRECTION_CLOCKWISE
            value = self._speed.replace(' ', '')
        command = self._commands_ini.get(section, value)
        
        _LOGGER.debug("send_ir func called, section: " +  section + ", value: " + value)
        
        for retry in range(DEFAULT_RETRY):
            try:
                payload = b64decode(command)
                self._broadlink_device.send_data(payload)
                break
            except (socket.timeout, ValueError):
                try:
                    self._broadlink_device.auth()
                except socket.timeout:
                    if retry == DEFAULT_RETRY-1:
                        _LOGGER.error("Failed to send packet to Broadlink RM Device")


    @property
    def name(self) -> str:
        """Get entity name."""
        return self._name

    @property
    def should_poll(self):
        """No polling needed for a demo fan."""
        return False

    @property
    def speed(self) -> str:
        """Return the current speed."""
        return self._speed

    @property
    def speed_list(self) -> list:
        """Get the list of available speeds."""
        return self._speed_list

    @asyncio.coroutine
    def async_turn_on(self, speed: str=None) -> None:
        """Turn on the entity."""
        _LOGGER.debug("Turn on with speed: %s" % speed)
        if speed is None:
            speed = self._speed
            if speed is None or speed is STATE_OFF:
                speed = self._default_speed
            _LOGGER.debug("No speed provided, use: %s" % speed)
        yield from self.async_set_speed(speed)

    @asyncio.coroutine
    def async_turn_off(self) -> None:
        """Turn off the entity."""
        _LOGGER.debug("Turn off")
        #self.oscillate(False)
        yield from self.async_set_speed(STATE_OFF)

    @asyncio.coroutine
    def async_set_speed(self, speed: str) -> None:
        """Set the speed of the fan."""
        _LOGGER.debug("Set speed: %s" % speed)
        self._speed = speed
        yield from self.async_send_ir_after_delay()
        self.async_schedule_update_ha_state()

    def set_direction(self, direction: str) -> None:
        """Set the direction of the fan."""
        _LOGGER.debug("Set direction: %s" % direction)
        self.direction = direction
        yield from self.async_send_ir_after_delay()
        self.async_schedule_update_ha_state()

    def oscillate(self, oscillating: bool) -> None:
        """Set oscillation."""
        self.oscillating = oscillating
        yield from self.async_send_ir_after_delay()
        self.async_schedule_update_ha_state()

    @property
    def current_direction(self) -> str:
        """Fan direction."""
        return self.direction

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return self._supported_features