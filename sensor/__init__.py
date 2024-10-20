"""Sensor platform for hassmic integration."""

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
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .. import init_entity
from ..const import STATE_DETECTED, STATE_ERROR, STATE_LISTENING

from .intent import Intent
from .pipeline_state import PipelineState
from .simple_state import SimpleState
from .stt import STT
from .wake import Wake

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize hassmic config entry for sensors."""

    SENSOR_TYPES = [
        Intent,
        PipelineState,
        SimpleState,
        STT,
        Wake,
    ]

    async_add_entities(
        [sensor_type(hass, config_entry) for sensor_type in SENSOR_TYPES]
    )
