"""Defines the `wake` sensor"""

from __future__ import annotations

from . import base
import enum
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.assist_pipeline.pipeline import (
    PipelineEvent,
    PipelineEventType,
)

from ..const import STATE_LISTENING, STATE_DETECTED

_LOGGER = logging.getLogger(__name__)


class Wake(base.SensorBase):
    """Defines a sensor with the wakeword state."""

    @property
    def hassmic_entity_name(self):
        return "wake"

    @property
    def icon(self):
        return "mdi:chat-alert-outline"

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        super().__init__(hass, config_entry)

    def on_pipeline_event(self, event: PipelineEvent):
        """Handle a pipeline event."""

        # Wakeword start and end set the WAKE sensor
        match event.type:
            case PipelineEventType.WAKE_WORD_START:
                self._attr_native_value = STATE_LISTENING
                self._attr_extra_state_attributes = {
                    "entity_id": event.data.get("entity_id", None)
                }

            case PipelineEventType.WAKE_WORD_END:
                self._attr_native_value = STATE_DETECTED
