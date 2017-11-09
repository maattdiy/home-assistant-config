import asyncio
import logging
import binascii
import socket
import os.path
import voluptuous as vol
import homeassistant.util as util
import homeassistant.helpers.config_validation as cv

from homeassistant.components.media_player import (
    SUPPORT_TURN_ON, SUPPORT_TURN_OFF, SUPPORT_VOLUME_MUTE, 
    SUPPORT_VOLUME_STEP, SUPPORT_SELECT_SOURCE, SUPPORT_PREVIOUS_TRACK,
    SUPPORT_NEXT_TRACK, MediaPlayerDevice, PLATFORM_SCHEMA)
from homeassistant.const import (
    CONF_HOST, CONF_MAC, CONF_TIMEOUT, STATE_OFF, STATE_ON,
    STATE_PLAYING, STATE_PAUSED, STATE_UNKNOWN, CONF_NAME, CONF_FILENAME)
from configparser import ConfigParser
from base64 import b64encode, b64decode

REQUIREMENTS = ['broadlink==0.5']

_LOGGER = logging.getLogger(__name__)

CONF_IRCODES_INI = 'ircodes_ini'

DEFAULT_NAME = 'Broadlink IR Media Player'
DEFAULT_TIMEOUT = 10
DEFAULT_RETRY = 3

SUPPORT_BROADLINK_TV = SUPPORT_TURN_OFF | SUPPORT_TURN_ON | \
    SUPPORT_VOLUME_MUTE | SUPPORT_VOLUME_STEP | \
    SUPPORT_PREVIOUS_TRACK | SUPPORT_NEXT_TRACK

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_MAC): cv.string,
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
    vol.Required(CONF_IRCODES_INI): cv.string,
})

@asyncio.coroutine 
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):    
    """Set up the Broadlink IR Media Player platform."""
    name = config.get(CONF_NAME)
    ip_addr = config.get(CONF_HOST)
    mac_addr = binascii.unhexlify(config.get(CONF_MAC).encode().replace(b':', b''))
    
    import broadlink
    
    broadlink_device = broadlink.rm((ip_addr, 80), mac_addr)
    broadlink_device.timeout = config.get(CONF_TIMEOUT)

    try:
        broadlink_device.auth()
    except socket.timeout:
        _LOGGER.error("Failed to connect to Broadlink RM Device")
    
    ircodes_ini_file = config.get(CONF_IRCODES_INI)
    
    if ircodes_ini_file.startswith("/"):
        ircodes_ini_file = ircodes_ini_file[1:]
        
    ircodes_ini_path = hass.config.path(ircodes_ini_file)
    
    if os.path.exists(ircodes_ini_path):
        ircodes_ini = ConfigParser()
        ircodes_ini.optionxform = str
        ircodes_ini.read(ircodes_ini_path)
    else:
        _LOGGER.error("The ini file was not found. (" + ircodes_ini_path + ")")
        return
    
    async_add_devices([BroadlinkIRMediaPlayer(hass, name, broadlink_device, ircodes_ini)], True)
    
    
class BroadlinkIRMediaPlayer(MediaPlayerDevice):

    def __init__(self, hass, name, broadlink_device, ircodes_ini):
        self._name = name
        self._state = STATE_OFF
        self._muted = False
        self._volume = 0
        self._sources_list = []
        
        self._broadlink_device = broadlink_device
        self._commands_ini = ircodes_ini
        
        self._source = None
        
        self._first_pop_up = True
        self._disallow_on_ir = False
        
        if ircodes_ini.has_section('sources'):
            sources_list = []
            for (key, value) in ircodes_ini.items('sources'):
                sources_list.append(key)
                
            self._sources_list = sources_list

    def send_ir(self, section, value):
        command = self._commands_ini.get(section, value)
        
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
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state
    
    @property
    def is_volume_muted(self):
        return False

    @property
    def volume_level(self):
        return self._volume
    
    @property
    def source_list(self):
        return self._sources_list
        
    @property
    def source(self):
        return self._source
        
    @property
    def media_title(self):
        return None
    
    @property
    def supported_features(self):
        if self._sources_list:
            return SUPPORT_BROADLINK_TV | SUPPORT_SELECT_SOURCE
        return SUPPORT_BROADLINK_TV
        
    def turn_off(self):
        self.send_ir('general', 'turn_off')
        self._state = STATE_OFF
        self.schedule_update_ha_state()
        
    def turn_on(self):
        if self._disallow_on_ir == False:
            self.send_ir('general', 'turn_on')
        
        self._state = STATE_ON
        self._source = None
        self.schedule_update_ha_state()
    
    def media_play(self):
        return

    def media_pause(self):
        return
        
    def media_stop(self):
        return
        
    def media_previous_track(self):
        if self._state == STATE_OFF:
            self._disallow_on_ir = True
            self._state = STATE_ON
            self._disallow_on_ir = False
        
        self.send_ir('general', 'previous_channel')
        self.schedule_update_ha_state()

    def media_next_track(self):
        if self._state == STATE_OFF:
            self._disallow_on_ir = True
            self._state = STATE_ON
            self._disallow_on_ir = False
        
        self.send_ir('general', 'next_channel')
        self.schedule_update_ha_state()

    def volume_down(self):
        self.send_ir('general', 'volume_down')
        self.schedule_update_ha_state()
     
    def volume_up(self):
        self.send_ir('general', 'volume_up')
        self.schedule_update_ha_state()

    def set_volume_level(self, volume):
        return

    def mute_volume(self, mute):
        self.send_ir('general', 'mute')
        self._muted = mute
        self.schedule_update_ha_state()
        
    def select_source(self, source):
        if self._state == STATE_OFF:
            self._disallow_on_ir = True
            self._state = STATE_ON
            self._disallow_on_ir = False
            
        if self._first_pop_up == True:
            self._source = None
            self._first_pop_up = False
        else:
            self.send_ir('sources', source)
            self._source = source
            self.schedule_update_ha_state()