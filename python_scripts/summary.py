## https://github.com/maattdiy/home-assistant-config

## Resources:
## https://home-assistant.io/components/python_script/
## https://home-assistant.io/docs/configuration/state_object/

home_count = 0
home_desc = ""
inuse_count = 0
inuse_desc = ""
summary = ""

##################################################
## People count
##################################################

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

##################################################
## Devices in use count
##################################################

domnains = ['switch', 'media_player']
for domain in domnains:
    for entity_id in hass.states.entity_ids(domain):
        show = False
        state = hass.states.get(entity_id)
        
        # Media players
        if (state.state == 'playing'):
            show = True
            
        # Switchs with icons
        if (state.state == 'on'):
            ## Only switchs with icons are relevants (ignore internal switchs). Find by tag "icon" in dictionary because "state.attributes.icon" didn't work
            if (str(state.attributes).find("'icon'")) >= 0:
                show = True
        
        if (show):
            if (inuse_desc.find(state.name + ', ') == -1):
                #logger.info("state.attributes = " + str(state.attributes))
                inuse_count = inuse_count + 1
                inuse_desc = inuse_desc + state.name + ', '

if inuse_count > 0:
    inuse_desc = str(inuse_count) + ' in use: ' + inuse_desc[:-2]
    summary = summary + '\n ' + inuse_desc

##################################################
## Alarm clock
##################################################

if (hass.states.get('input_boolean.alarmclock_wd_enabled').state != 'on') and (hass.states.get('input_boolean.alarmclock_we_enabled').state != 'on'):
    summary = summary + '\n ' + '!Alarm clock is disabled'

##################################################
## Profile/mode
##################################################

state = hass.states.get('input_select.ha_mode')
if (state.state != 'Normal'):
    summary = summary + '\n ' + '* ' + state.state + ' profile is activated'
    hass.states.set('sensor.profile_badge', '', {
        'entity_picture':  '/local/profiles/{}.png'.format(state.state.lower()),
        'friendly_name': ' ',
        'unit_of_measurement': 'Mode'
    })

##################################################
## Sensors updates
##################################################

# People badge update
hass.states.set('sensor.people_badge', home_count, {
    'friendly_name': ' ',
    'unit_of_measurement': 'Home',
})

# In use badge update
hass.states.set('sensor.inuse_badge', inuse_count, {
    'friendly_name': ' ',
    'unit_of_measurement': 'In use'
})

# Summary sensors update
hass.states.set('sensor.summary', summary, {
    'custom_ui_state_card': 'state-card-value_only'
})
