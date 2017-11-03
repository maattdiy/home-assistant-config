## Calendar HASS Module

## https://home-assistant.io/components/calendar.google/
## https://github.com/jjmontesl/home-assistant-config/blob/master/config/packages/calendars.yaml

##################################################
## Component
##################################################

google:
  client_id: !secret google_client_id
  client_secret: !secret google_client_secret
  track_new_calendar: False
  
##################################################
## Customizes
##################################################

##################################################
## Sensors
##################################################

sensor:
  - platform: template
    sensors:
      tv_schedule_live:
        value_template: >
          {{ strptime(states.calendar.Casa.attributes.start_time, "%Y-%m-%d %H:%M:%S").strftime("%a %H:%M") }} •
          {{ states.calendar.Casa.attributes.message }}
        friendly_name: 'TV Live'
        icon_template: "{{ 'mdi:television' }}"

##################################################
## Automations
##################################################

