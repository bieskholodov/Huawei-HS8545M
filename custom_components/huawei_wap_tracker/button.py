import logging
import telnetlib
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.helpers.device_registry import DeviceInfo

_LOGGER = logging.getLogger(__name__)
DOMAIN = "huawei_wap_tracker"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Setup the button platform from a Config Entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([
        HuaweiRefreshButton(coordinator, entry),
        HuaweiRebootButton(coordinator, entry)
    ])


class HuaweiRefreshButton(CoordinatorEntity, ButtonEntity):
    """Button to force update coordinator data."""

    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = "Huawei Router - Update data"
        self._attr_translation_key = "update_data"  # Ключ для файла перевода
        self._attr_unique_id = f"hw_refresh_btn_{entry.entry_id}"
        self._attr_icon = "mdi:refresh"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_refresh()

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Huawei HS8545M Router",
            manufacturer="Huawei",
            model="HS8545M",
        )


class HuaweiRebootButton(CoordinatorEntity, ButtonEntity):
    """Button to hardware reboot the router."""

    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._config = entry.data
        self._entry = entry
        self._attr_name = "Huawei Router - Reboot router"
        self._attr_translation_key = "reboot_router"  # Ключ для файла перевода
        self._attr_unique_id = f"hw_reboot_btn_{entry.entry_id}"
        self._attr_icon = "mdi:restart"

    def _send_reboot_command(self) -> None:
        """Send the verified board reset command via Telnet in an executor thread."""
        try:
            tn = telnetlib.Telnet(self._config["host"], 23, timeout=5)
            tn.read_until(b"Login:", timeout=3)
            tn.write(self._config["username"].encode('ascii') + b"\n")
            tn.read_until(b"Password:", timeout=3)
            tn.write(self._config["password"].encode('ascii') + b"\n")
            
            tn.read_until(b"WAP>", timeout=3)
            tn.write(b"reset\n")
            tn.close()
            _LOGGER.info("Hardware reboot command 'reset' sent to Huawei router")
        except Exception as e:
            _LOGGER.error("Error sending reboot command via Telnet: %s", e)

    async def async_press(self) -> None:
        """Handle the button press in HA interface."""
        await self.hass.async_add_executor_job(self._send_reboot_command)

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Huawei HS8545M Router",
            manufacturer="Huawei",
            model="HS8545M",
        )
