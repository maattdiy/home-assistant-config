## Broadlink Media Player HASS Module
## Original forum thread: https://github.com/vpnmaster/homeassistant-custom-components
## Official repo: https://community.home-assistant.io/t/broadlink-ir-climate-component/27406

##################################################
## Component
##################################################

media_player:
  - platform: broadlink
    name: TV
    host: !secret ip_broadlink
    mac: !secret mac_broadlink
    timeout: 60
    ircodes_ini: 'resources/broadlink_media_codes/samsung.ini'

##################################################
## Scripts
##################################################

#script:
