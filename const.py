"""Constants for the hassmic integration."""

from homeassistant.const import Platform

# The name of this integration
DOMAIN = "hassmic"

# The platforms this integration provides
PLATFORMS = [
    Platform.SENSOR,
    Platform.SWITCH,
]

# Possible states for sensors
STATE_LISTENING = "listening"
STATE_DETECTED = "detected"
STATE_ERROR = "error"
