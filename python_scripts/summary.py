## https://home-assistant.io/components/python_script/
## https://community.home-assistant.io/t/count-people-that-are-home/20184
## https://home-assistant.io/docs/configuration/state_object/

home_count = 0
home_desc = ""
inuse_count = 0
inuse_desc = ""
summary = ""

# People at home (only by phone)
for entity_id in hass.states.entity_ids('device_tracker'):
    if entity_id.find("phone") >= 0:
        state = hass.states.get(entity_id)
        if state.state == 'home':
            home_count = home_count + 1
            home_desc = home_desc + state.name + ', '
            #relative_time(state.last_changed) Is possible show the relative time?

if home_count > 0:
    home_desc = str(home_count) + ' at home: ' + home_desc[:-2]
else:
    home_desc = 'Nobody in home'

summary = home_desc

# Devices in use (switchs with icons)
for entity_id in hass.states.entity_ids('switch'):
    state = hass.states.get(entity_id)
    if (state.state == 'on'):
        ## Only switchs with icons are relevants (ignore internal switchs). Find by tag "icon" in dictionary because "state.attributes.icon" didn't work
        if (str(state.attributes).find("'icon'")) >= 0:
            if (inuse_desc.find(state.name + ', ') == -1):
                #logger.info("state.attributes = " + str(state.attributes))
                inuse_count = inuse_count + 1
                inuse_desc = inuse_desc + state.name + ', '

# Players in use
for entity_id in hass.states.entity_ids('media_player'):
    state = hass.states.get(entity_id)
    if (state.state == 'playing'):
        inuse_count = inuse_count + 1
        inuse_desc = inuse_desc + state.name + ', '

if inuse_count > 0:
    inuse_desc = str(inuse_count) + ' in use: ' + inuse_desc[:-2]
    summary = summary + '\n ' + inuse_desc

# Alarm clock
if (hass.states.get('input_boolean.alarmclock_wd_enabled').state != 'on') and (hass.states.get('input_boolean.alarmclock_we_enabled').state != 'on'):
    summary = summary + '\n ' + '!Alarm clock is disabled'

# Profile
state = hass.states.get('input_select.ha_mode')
if (state.state != 'Normal'):
    summary = summary + '\n ' + '* ' + state.state + '  profile is activated (custom behavior)'

# Sensor update
hass.states.set('sensor.summary', summary, {
    'custom_ui_state_card': 'state-card-value_only'
})
