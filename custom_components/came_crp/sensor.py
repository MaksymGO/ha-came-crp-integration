"""CRP communication and raw status diagnostics."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_INVALID_FRAMES,
    ATTR_LAST_COMMANDS,
    ATTR_LAST_RX,
    ATTR_LAST_TX,
    ATTR_VALID_FRAMES,
    DOMAIN,
)
from .coordinator import CAMECRPCoordinator

DESCRIPTIONS = (
    SensorEntityDescription(
        key="state_raw",
        name="Raw state reply",
        icon="mdi:code-braces",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="last_seen",
        name="Last valid frame",
        icon="mdi:clock-check-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=ATTR_LAST_TX,
        name="Last transmitted frame",
        icon="mdi:upload-network-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=ATTR_LAST_RX,
        name="Last received frame",
        icon="mdi:download-network-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=ATTR_LAST_COMMANDS,
        name="Last decoded commands",
        icon="mdi:code-json",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=ATTR_VALID_FRAMES,
        name="Valid CRP frames",
        icon="mdi:check-network-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=ATTR_INVALID_FRAMES,
        name="Invalid CRP frames",
        icon="mdi:alert-network-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: CAMECRPCoordinator = entry.runtime_data
    async_add_entities(
        CAMECRPSensor(coordinator, entry, description) for description in DESCRIPTIONS
    )


class CAMECRPSensor(CoordinatorEntity[CAMECRPCoordinator], SensorEntity):
    """Expose diagnostics without assuming undocumented state meanings."""

    entity_description: SensorEntityDescription

    def __init__(
        self,
        coordinator: CAMECRPCoordinator,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=str(entry.data.get("name", "CAME CRP Gate")),
            manufacturer="CAME",
            model=str(entry.data.get("model", "Generic CRP")),
        )

    @property
    def native_value(self):
        value = self.coordinator.data.get(self.entity_description.key)
        if isinstance(value, (dict, list, tuple)):
            return str(value)
        return value

    @property
    def extra_state_attributes(self):
        return {
            "address": self.coordinator.address,
            "transport": self.coordinator.data.get("transport"),
            "baudrate": self.coordinator.data.get("baudrate"),
            "model": self.coordinator.data.get("model"),
            "information_raw": self.coordinator.data.get("information_raw"),
            "information_signature": self.coordinator.data.get("information_signature"),
            "last_transmitted_frame": self.coordinator.data.get(ATTR_LAST_TX),
            "last_received_frame": self.coordinator.data.get(ATTR_LAST_RX),
            "last_commands": self.coordinator.data.get(ATTR_LAST_COMMANDS),
        }
