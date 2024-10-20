"""Provides the base class for hassmic sensors."""

from __future__ import annotations

import enum
import logging
import re

from homeassistant.components.assist_pipeline.pipeline import (
    PipelineEvent,
    PipelineEventType,
)
from homeassistant.components.sensor import ENTITY_ID_FORMAT, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_IDLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, generate_entity_id
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .. import init_entity
from .. import const

_LOGGER = logging.getLogger(__name__)


class SensorBase(SensorEntity):
    """A generic hassmic Sensor.

    All sensors should inherit from this class.

    """

    _attr_native_value = STATE_IDLE
    _attr_should_poll = False

    @property
    def hassmic_entity_name(self):
        raise NotImplementedError(
            f"Class {type(self).__name__} has no hassmic_entity_name"
        )

    @property
    def icon(self):
        return "mdi:help"

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize hassmic Sensor."""
        super().__init__()

        unique_id = config_entry.unique_id
        self.unique_id = f"{unique_id}-{self.hassmic_entity_name}"
        self.name = (
            config_entry.title
            + " "
            + self.hassmic_entity_name.replace("_", " ").upper()
        )

        self.device_info = DeviceInfo(
            identifiers={(const.DOMAIN, unique_id)},
        )

        id_candidate = re.sub(
            r"[^A-Za-z0-9_]",
            "_",
            f"{config_entry.title}_{self.hassmic_entity_name}".lower(),
        )
        self.entity_id = generate_entity_id(ENTITY_ID_FORMAT, id_candidate, hass=hass)
        config_entry.runtime_data.register_entity(self)

    def handle_connection_state_change(self, new_state: bool):
        """Handle a connection state change."""
        self.available = new_state
        self.schedule_update_ha_state()

    def on_pipeline_event(self, event: PipelineEvent):
        """This method gets overridden to handle pipeline events for sensors."""
        pass

    def handle_pipeline_event(self, event: PipelineEvent):  # noqa: C901
        """Handle a `PipelineEvent` by calling on_pipeline_event()."""

        # if we're not connected (sensor is unavailable), ignore pipeline state
        # updates
        if not self.available:
            return

        # If we encountered an error, set all sensors to error
        if event.type == PipelineEventType.ERROR:
            if event.data.get("code", None) != "wake-word-timeout":
                self._attr_native_value = STATE_ERROR

        # TODO - figure out what the best thing to do with run_start and
        # run_end is.

        self.on_pipeline_event(event)
        self.schedule_update_ha_state()
        return
