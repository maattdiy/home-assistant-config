## Broadlink Climate HASS Module
## Original forum thread: https://github.com/vpnmaster/homeassistant-custom-components
## Official repo: https://community.home-assistant.io/t/broadlink-ir-climate-component/27406

##################################################
## Component
##################################################

climate:
  - platform: broadlink
    name: AC
    host: !secret ip_broadlink
    mac: !secret mac_broadlink
    timeout: 60
    ircodes_ini: 'resources/broadlink_climate_codes/midea.ini'
    min_temp: 18
    max_temp: 30
    target_temp: 20
    #temp_sensor: sensor.living_room_temperature
    default_operation: idle
    default_fan_mode: mid
    customize:
      operations:
        - idle
        - cool
        - heat
      fan_modes:
        - low
        - mid
        - high
        - auto

##################################################
## Scripts
##################################################

#script:
