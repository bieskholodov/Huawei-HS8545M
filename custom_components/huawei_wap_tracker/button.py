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
    """Настройка платформы button из Config Entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([
        HuaweiRefreshButton(coordinator, entry),
        HuaweiRebootButton(coordinator, entry)
    ])


class HuaweiRefreshButton(CoordinatorEntity, ButtonEntity):
    """Кнопка принудительного обновления данных координатора."""

    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Инициализация."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = "Huawei Роутер - Обновить данные"
        self._attr_unique_id = f"hw_refresh_btn_{entry.entry_id}"
        self._attr_icon = "mdi:refresh"

    async def async_press(self) -> None:
        """Вызывается при нажатии кнопки обновления."""
        await self.coordinator.async_refresh()

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Роутер Huawei HS8545M",
            manufacturer="Huawei",
            model="HS8545M",
        )


class HuaweiRebootButton(CoordinatorEntity, ButtonEntity):
    """Кнопка аппаратной перезагрузки роутера."""

    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Инициализация."""
        super().__init__(coordinator)
        self._config = entry.data
        self._entry = entry
        self._attr_name = "Huawei Роутер - Перезагрузка роутера"
        self._attr_unique_id = f"hw_reboot_btn_{entry.entry_id}"
        self._attr_icon = "mdi:restart"

    def _send_reboot_command(self) -> None:
        """Отправка проверенной команды reset платы через Telnet в фоновом потоке."""
        try:
            tn = telnetlib.Telnet(self._config["host"], 23, timeout=5)
            tn.read_until(b"Login:", timeout=3)
            tn.write(self._config["username"].encode('ascii') + b"\n")
            tn.read_until(b"Password:", timeout=3)
            tn.write(self._config["password"].encode('ascii') + b"\n")
            
            # Ждем появления стандартной командной строки WAP>
            tn.read_until(b"WAP>", timeout=3)
            
            # Отправляем точную команду перезагрузки платы роутера
            tn.write(b"reset\n")
            
            # Закрываем соединение, так как роутер мгновенно начнет тушить сетевую плату
            tn.close()
            _LOGGER.info("Команда аппаратной перезагрузки 'reset' отправлена на роутер Huawei")
        except Exception as e:
            _LOGGER.error("Ошибка отправки команды перезагрузки по Telnet: %s", e)

    async def async_press(self) -> None:
        """Вызывается при нажатии кнопки перезагрузки в интерфейсе HA."""
        # Выполняем Telnet команду в фоновом потоке, чтобы интерфейс HA не зависал
        await self.hass.async_add_executor_job(self._send_reboot_command)

    @property
    def device_info(self) -> DeviceInfo:
        """Связывание кнопки с общей карточкой вашего роутера."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Роутер Huawei HS8545M",
            manufacturer="Huawei",
            model="HS8545M",
        )
