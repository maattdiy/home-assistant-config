## Repo: https://github.com/maattdiy/home-assistant-config
## Screenshot: https://github.com/maattdiy/home-assistant-config/blob/master/screenshots/summary.png
## Script call: https://github.com/maattdiy/home-assistant-config/blob/master/config/packages/summary.yaml

## Resources:
## https://home-assistant.io/components/python_script/
## https://home-assistant.io/docs/configuration/state_object/

debug = False
show_badges = True
show_card = True

group_count = 0
group_desc = ''
summary = ''
idx = 0
dt_prevstate = None

if debug:
    event = data.get('event')
    logger.error("\n\nSUMMARY: " + str(event))

##################################################
## Groups summary (people and devices)
## Groups config: https://github.com/maattdiy/home-assistant-config/blob/master/config/groups.yaml#L267
##################################################

# Summary by groups
groups = ['group.family', 'group.devices_default', 'group.devices_alwayson']
groups_format = ['{} at home: {}', '{} in use: {}', '!{} to check it out: {}'] # Message prefix
groups_filter = ['home', 'on|playing', 'off|not_home'] # Filter to list
groups_badge = ['Home', 'In use', 'Status'] # Badge 'belt' (unit_of_measurement)
groups_badge_pic = ['', '', 'ok|bug|critical'] # Pictures: none, on picure or a list of picture (in this case the picture position will match the count)
groups_min_show = [0, 1, 1] # Mininum count to show
groups_theme = ['entity_green', 'entity_purple', 'entity_green|entity_orange|entity_red'] # Theme template
groups_desc = ['!Nobody in home', '', ''] # Can set the default description, for use in case count = 0
#groups_desc = ['!Nobody in home', '', '+System ok']
groups_count = [0, 0, 0]

for group in groups:
    group_count = 0
    group_desc = ''
    
    for entity_id in hass.states.get(group).attributes['entity_id']:
        state = hass.states.get(entity_id)
        filter = groups_filter[idx]
        
        if (state.state in filter.split('|') or debug):
            dt = state.last_changed
            dt = dt + datetime.timedelta(hours=-3) # For time zone :( How to do native?
            time = '%02d:%02d' % (dt.hour, dt.minute)
            
            # If state changed in the past days show the date too
            if dt.date() < datetime.datetime.now().date():
                time = '{} {}'.format('%02d/%02d' % (dt.day, dt.month), time)
            
            group_count = group_count + 1
            group_desc = '{} {} ({}), '.format(group_desc, state.name, time)
        else:
            if (dt_prevstate is None):
                dt_prevstate = state.last_changed
            else:
                if (state.last_changed > dt_prevstate):
                    dt_prevstate = state.last_changed
            
    # Final format for this group
    if (group_count >= groups_min_show[idx]):
        if (group_count == 0):
            group_desc = groups_desc[idx]
            # If there is none 'On/Home' state in group, show since...
            if (group_desc != ''):
                dt = dt_prevstate + datetime.timedelta(hours=-3)
                group_desc = '{} since {}'.format(group_desc, '%02d:%02d' % (dt.hour, dt.minute))
        else:
            group_desc = groups_format[idx].format(group_count, group_desc[:-2])
        
        groups_desc[idx] = group_desc
        groups_count[idx] = group_count
        
    idx = idx + 1

##################################################
## Badges updates
## Badges images: https://github.com/maattdiy/home-assistant-config/tree/master/www/badges
##################################################

idx = 0
order = 2

if show_badges:
    for badge in groups_badge:
        if (badge != ''):
            entity_id = 'sensor.{}_badge'.format(badge.replace(' ', '').lower());
            hidden = False if (groups_count[idx] >= groups_min_show[idx] or debug) else True
            fname = groups_desc[idx] if debug else ' '
            picture = groups_badge_pic[idx].replace(' ', '').lower()
            theme = groups_theme[idx].replace('value', 'entities["{}"].state'.format(entity_id)) if (groups_theme[idx] != '') else 'default'
            
            # Check for theme X index/count
            if (theme.find('|') > 0):
                list = theme.split('|')
                if (len(list) in [1, groups_count[idx]]):
                    theme = list[len(list)-1]
                else:
                    theme = list[groups_count[idx]]
            
            # Check for picture X index/count
            if (picture != ''):
                list = picture.split('|')
                if (len(list) in [1, groups_count[idx]]):
                    picture = list[len(list)-1]
                else:
                    picture = list[groups_count[idx]]
                
                if (picture != ''):
                    picture = '/local/badges/{}.png'.format(picture)
            
            hass.states.set(entity_id, groups_count[idx], {
              'friendly_name': fname,
              'unit_of_measurement': badge, 
              'entity_picture': picture,
              'hidden': hidden,
              'templates': { 'theme': theme }
            })
            # Order seems not working
            # 'order': order
        
        order = order + 1
        idx = idx + 1

##################################################
## Alarm clock
## Package: https://github.com/maattdiy/home-assistant-config/blob/master/config/packages/alarmclock.yaml
##################################################

alarms_prefix = ['alarmclock_wd', 'alarmclock_we']
alarms_wfilter = ['1|2|3|4|5', '6|7']
alarms_desc = ''
idx = 0

for entity_id in alarms_prefix:
    state = hass.states.get('input_boolean.{}_enabled'.format(entity_id))
    if (not state is None):
        if (state.state == 'on'):
            # Show the alarm for the next day
            if (str(datetime.datetime.now().isoweekday()) in alarms_wfilter[idx].split('|')):
                state = hass.states.get('sensor.{}_time_template'.format(entity_id))
                alarms_desc = '{}{}, '.format(alarms_desc, state.state)
    idx = idx + 1

if (alarms_desc == ''):
    alarms_desc = '!Alarm clock is disabled'
else:
    alarms_desc = 'Alarm clock at ' + alarms_desc[:-2]

##################################################
## Profile/mode
## General package: https://github.com/maattdiy/home-assistant-config/blob/master/config/packages/profiles.yaml
## Developer package: https://github.com/maattdiy/home-assistant-config/blob/master/config/packages/developer.yaml
## Badges images: https://github.com/maattdiy/home-assistant-config/tree/master/www/profiles
##################################################

profile_desc = ''
state = hass.states.get('input_select.ha_mode')

if (not state is None):
    hidden = False if (state.state != 'Normal') else True
    
    hass.states.set('sensor.profile_badge', '', {
      'entity_picture':  '/local/profiles/{}.png'.format(state.state.replace(' ', '').lower()),
      'friendly_name': ' ',
      'unit_of_measurement': 'Mode',
      'hidden': hidden,
      'order': order
    })
    
    if not hidden:
        profile_desc = '*{} profile is activated'.format(state.state)

##################################################
## Activity
## Package: https://github.com/maattdiy/home-assistant-config/blob/master/python_scripts/activity.py
##################################################

activity_desc = ''
state = hass.states.get('input_select.activity')
time = '?'

if (not state is None):
    if (state.state != 'Unknown'):
        dt = hass.states.get('automation.activity_change').attributes.get('last_triggered')        
        if (not dt is None):
            time = "%02d:%02d" % (dt.hour, dt.minute)
        
        # Alternative way for time
        #time = hass.states.get('sensor.activity_badge').attributes.get('friendly_name')
        activity_desc = 'Activity: {} ({})'.format(state.state, time)

##################################################
## Summary update
## Custom card: https://github.com/maattdiy/home-assistant-config/blob/master/www/custom_ui/state-card-text.html
##################################################

for group_desc in groups_desc:
    if (group_desc != '' and not group_desc.endswith(': ')):
        summary = '{}{}\n'.format(summary, group_desc)

summary = '{}\n{}\n{}\n{}'.format(summary, alarms_desc, profile_desc, activity_desc)

if show_card:
    hass.states.set('sensor.summary', '', {
      'custom_ui_state_card': 'state-card-text',
      'text': summary
    })
