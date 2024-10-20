"""Defines the `pipeline_state` sensor"""

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

_LOGGER = logging.getLogger(__name__)


class PipelineState(base.SensorBase):
    """Defines a sensor with the full pipeline state."""

    @property
    def hassmic_entity_name(self):
        return "pipeline_state"

    @property
    def icon(self):
        return "mdi:assistant"

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        super().__init__(hass, config_entry)

    def on_pipeline_event(self, event: PipelineEvent):
        """Handle a pipeline event."""

        # Just set the sensor state to the event type and don't do any
        # processing.
        self._attr_native_value = event.type
        self.attr_extra_state_attributes = event.data
