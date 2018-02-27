# Get params
event = data.get('event')

logger.error("TELEGRAM: " + data)
logger.error("TELEGRAM: " + event)

# Sensor update
hass.states.set('sensor.summary', '', {
    'custom_ui_state_card': 'state-card-text'
})
