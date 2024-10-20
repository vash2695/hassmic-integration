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

from . import init_entity
from .const import STATE_DETECTED, STATE_ERROR, STATE_LISTENING

_LOGGER = logging.getLogger(__name__)

# A list of the sensors provided by each instance of this integration
class WhichSensor(enum.StrEnum):
    """The list of possible sensors types."""

    # State of wakeword detection
    WAKE = "wake"

    # Speech to text of current pipeline run
    STT = "stt"

    # Intent of curent run
    INTENT = "intent"

    # Simple state, primarily useful for view assist or other automations
    SIMPLE_STATE = "simple_state"

    # Overall current pipeline state
    PIPELINE_STATE = "pipeline_state"

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize hassmic config entry for sensors."""

    async_add_entities([hassmicSensorEntity(hass, config_entry, key) for key in WhichSensor])


class hassmicSensorEntity(SensorEntity):
    """hassmic Sensor."""

    _attr_native_value = STATE_IDLE
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, key: WhichSensor) -> None:
        """Initialize hassmic Sensor."""
        super().__init__()
        init_entity(self, key.value, config_entry)
        self._key: WhichSensor = key

        id_candidate = re.sub(
                r"[^A-Za-z0-9_]", "_", f"{config_entry.title}_{key.value}".lower())
        self.entity_id = generate_entity_id(ENTITY_ID_FORMAT, id_candidate, hass=hass)

    def handle_connection_state_change(self, new_state: bool):
      """Handle a connection state change."""
      self.available = new_state
      self.schedule_update_ha_state()

    def handle_pipeline_event(self, event: PipelineEvent): # noqa: C901
        """Handle a `PipelineEvent` and perform any required state updates.

        This is called on *every* sensor for *every* pipeline event.
        """

        # if we're not connected (sensor is unavailable), ignore pipeline state
        # updates
        if not self.available:
          return

        # For the pipeline state sensor, just set the state to the event type
        # and don't do any processing.
        if self._key == WhichSensor.PIPELINE_STATE:
            self._attr_native_value = event.type
            self.attr_extra_state_attributes = event.data
            self.schedule_update_ha_state()
            return

        # We also have a "simple state" sensor, for view assist
        # This translates key events in the pipeline into more-easily-parsible
        # "stage-status" strings.
        if self._key == WhichSensor.SIMPLE_STATE:
            def getSimpleState() -> str:
                match event.type:
                    case PipelineEventType.ERROR:
                        return "error-error"
                    case PipelineEventType.WAKE_WORD_START:
                        return "wake_word-listening"
                    case PipelineEventType.STT_START:
                        return "stt-listening"
                    case PipelineEventType.INTENT_START:
                        return "intent-processing"
                    case PipelineEventType.TTS_START:
                        return "tts-generating"
                    case PipelineEventType.TTS_END:
                        return "tts-speaking"
                    case _:
                        return None

            s = getSimpleState()
            if s is not None:
                self._attr_native_value = getSimpleState()



        match event.type:
            # TODO - figure out what the best thing to do with run_start and
            # run_end is.
            #
            ## If we're starting or ending a pipeline, reset all the sensors.
            #case PipelineEventType.RUN_START | PipelineEventType.RUN_END:
            #    self._attr_native_value = STATE_IDLE

            # If we encountered an error, set all sensors to error
            case PipelineEventType.ERROR:
                if event.data.get("code", None) != "wake-word-timeout":
                    self._attr_native_value = STATE_ERROR

            # Wakeword start and end set the WAKE sensor
            case PipelineEventType.WAKE_WORD_START:
                if self._key == WhichSensor.WAKE:
                    self._attr_native_value = STATE_LISTENING
                    self._attr_extra_state_attributes = {
                            "entity_id": event.data.get("entity_id", None)
                            }

            case PipelineEventType.WAKE_WORD_END:
                if self._key == WhichSensor.WAKE:
                    self._attr_native_value = STATE_DETECTED

            # We don't care about these for now, but enumerate them explicitly
            # in case we do later.
            case PipelineEventType.STT_START | PipelineEventType.STT_VAD_START | PipelineEventType.STT_VAD_END:
                pass

            # When STT ends, the event data has the interpreted STT text
            case PipelineEventType.STT_END:
                if self._key == WhichSensor.STT:
                    stt_out = event.data.get("stt_output", None)
                    if stt_out:
                        txt = stt_out.get("text", None)
                        self._attr_native_value = (
                            txt if len(txt) <= 255
                            else (txt[:252] + "...").strip()
                            )
                        self._attr_extra_state_attributes = {
                            "speech": txt,
                        }

            # Do nothing for INTENT_START
            case PipelineEventType.INTENT_START:
                pass

            # INTENT_END has the conversation response
            case PipelineEventType.INTENT_END:
                if self._key == WhichSensor.INTENT:
                    iout = event.data.get("intent_output", None)
                    if iout is None:
                        _LOGGER.warning("Got no intent_output data from INTENT_END event")
                        return
                    response = iout.get("response", None)
                    conversation_id = iout.get("conversation_id", None)
                    resp = {}
                    if response:
                        resp["response_type"] = response.get("response_type", None)
                        resp["response_data"] = response.get("data", None)
                        resp["speech"] = response.get("speech", None)

                    # speech type can be one of "plain" (default) or "ssml"
                    speech = ""
                    speech_type = None
                    if s := resp.get("speech"):
                        if ps := s.get("plain", None):
                            speech = ps.get("speech", None)
                            speech_type = "plain"
                        elif ssml := s.get("ssml", None):
                            speech = ssml.get("speech", None)
                            speech_type = "ssml"

                    if not speech or not speech_type:
                        _LOGGER.warning("No speech found in intent output")

                    self._attr_native_value = (
                        speech if len(speech) <= 255
                        else (speech[:252] + "...").strip()
                        )
                    self._attr_extra_state_attributes = {
                        **event.data,
                        'speech_output': speech,
                    }

            # Do nothing for TTS_START
            case PipelineEventType.TTS_START:
                pass

            # TTS_END has the media URL
            case PipelineEventType.TTS_END:
                pass



        self.schedule_update_ha_state()

