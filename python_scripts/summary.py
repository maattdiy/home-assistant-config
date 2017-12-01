## https://github.com/maattdiy/home-assistant-config

## Resources:
## https://home-assistant.io/components/python_script/
## https://home-assistant.io/docs/configuration/state_object/

group_count = 0
group_desc = ""
inuse_count = 0
inuse_desc = ""
summary = ""
idx = 0

##################################################
## Group count (people and devices)
##################################################

# Entities summary by group name
groups = ['group.family' , 'group.devices_alwayson']
groups_condition = ['home', 'not_home']
groups_format = ['{} at home: {}', '!{} offline: {}']

for group in groups:
    group_count = 0
    group_desc = ''
    
    for entity_id in hass.states.get(group).attributes['entity_id']:
        state = hass.states.get(entity_id)
        
        if state.state == groups_condition[idx]:
            dt = state.last_changed
            dt = dt + datetime.timedelta(hours=-2) # For time zone :( How to do native?
            time = '%02d:%02d' % (dt.hour, dt.minute)
            
            # If state changed in the past days show the date too
            if dt.date() < datetime.datetime.now().date():
                time = '{} {}'.format('%02d/%02d' % (dt.day, dt.month), time)
            
            group_count = group_count + 1
            group_desc = '{} {} ({}), '.format(group_desc, state.name, time)
    
    # Final format for this group
    if group_count > 0:    
        group_desc = groups_format[idx].format(group_count, group_desc[:-2])
    
    summary = '{}{}\n'.format(summary, group_desc)
    idx = idx + 1

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
hass.states.set('sensor.people_badge', group_count, {
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
