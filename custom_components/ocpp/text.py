"""Text platform for ocpp."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Final

from homeassistant.components.text import (
    DOMAIN as TEXT_DOMAIN,
    TextEntity,
    TextEntityDescription,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.restore_state import RestoreEntity

from .api import CentralSystem
from .const import (
    CONF_CPID,
    CONF_CPIDS,
    DATA_UPDATED,
    DOMAIN,
    ICON,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)
logging.getLogger(DOMAIN).setLevel(logging.INFO)


@dataclass
class OcppTextDescription(TextEntityDescription):
    """Class to describe a Text entity."""

    initial_value: str | None = None


TEXTS: Final = [
    OcppTextDescription(
        key="remote_id_tag",
        name="Remote Id Tag",
        icon=ICON,
        initial_value=None,
        native_min=1,
        native_max=20,
        pattern=r"^[A-Z0-9]+$",
    ),
]


async def async_setup_entry(hass, entry, async_add_devices):
    """Configure the text platform."""
    central_system = hass.data[DOMAIN][entry.entry_id]
    entities: list[ChargePointText] = []

    for charger in entry.data[CONF_CPIDS]:
        cp_id_settings = list(charger.values())[0]
        cpid = cp_id_settings[CONF_CPID]

        for desc in TEXTS:
            entities.append(
                ChargePointText(
                    hass=hass,
                    central_system=central_system,
                    cpid=cpid,
                    description=desc,
                )
            )

    async_add_devices(entities, False)


class ChargePointText(TextEntity, RestoreEntity):
    """Individual text entity for charge point."""

    _attr_has_entity_name = False
    entity_description: OcppTextDescription

    def __init__(
        self,
        hass: HomeAssistant,
        central_system: CentralSystem,
        cpid: str,
        description: OcppTextDescription,
    ):
        """Initialize a Text instance."""
        self.cpid = cpid
        self._hass = hass
        self.central_system = central_system
        self.entity_description = description

        parts = [TEXT_DOMAIN, DOMAIN, cpid, description.key]
        self._attr_unique_id = ".".join(parts)
        self._attr_name = self.entity_description.name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, cpid)},
            name=cpid,
        )
        object_id = f"{self.cpid}_{self.entity_description.key}"
        self.entity_id = f"{TEXT_DOMAIN}.{object_id}"
        self._attr_native_value = self.entity_description.initial_value
        self._attr_should_poll = False
        self._attr_entity_category = EntityCategory.CONFIG

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await super().async_added_to_hass()

        # Get the current value from the charge point if available
        if self.entity_description.key == "remote_id_tag":
            current_value = self.central_system.get_remote_id_tag(self.cpid)
            if current_value:
                self._attr_native_value = current_value

        # Restore state from previous session if no current value
        if self._attr_native_value is None:
            if (last_state := await self.async_get_last_state()) is not None:
                if last_state.state and last_state.state != "unknown":
                    self._attr_native_value = last_state.state
                    # Update the central system's charge point with the restored value
                    if self.entity_description.key == "remote_id_tag":
                        await self.central_system.set_remote_id_tag(
                            self.cpid, last_state.state
                        )

        @callback
        def _maybe_update(*args):
            active_lookup = None
            if args:
                try:
                    active_lookup = set(args[0])
                except Exception:
                    active_lookup = None

            if active_lookup is None or self.entity_id in active_lookup:
                self.async_schedule_update_ha_state(True)

        self.async_on_remove(
            async_dispatcher_connect(self.hass, DATA_UPDATED, _maybe_update)
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.central_system.get_available(self.cpid, None)

    async def async_set_value(self, value: str) -> None:
        """Set new value for remote ID tag."""
        self._attr_native_value = value
        self.async_write_ha_state()

        try:
            if self.entity_description.key == "remote_id_tag":
                await self.central_system.set_remote_id_tag(self.cpid, value)
                _LOGGER.info("Remote ID tag set to: %s", value)
        except Exception as ex:
            _LOGGER.warning(
                "Set remote ID tag failed: %s (kept optimistic UI at %s).",
                ex,
                value,
            )
