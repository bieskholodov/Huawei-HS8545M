# custom_components/huawei_wap_tracker/button.py

import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.helpers.device_registry import DeviceInfo

# Импортируем DOMAIN из __init__.py
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Настройка платформы button из Config Entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    client = hass.data[DOMAIN][entry.entry_id]["client"]
    
    # Добавляем две кнопки: обновление данных и перезагрузка
    async_add_entities([
        HuaweiUpdateDataButton(coordinator, entry),
        HuaweiRebootRouterButton(coordinator, entry, client)
    ])


class HuaweiUpdateDataButton(CoordinatorEntity, ButtonEntity):
    """Кнопка для принудительного обновления данных в Home Assistant."""

    _attr_has_entity_name = True
    _attr_translation_key = "update_data"  # Соответствует ключу в ru.json / en.json

    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Инициализация."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"hw_btn_update_data_{entry.entry_id}"

    async def async_press(self) -> None:
        """Действие при нажатии кнопки: принудительное обновление координатора."""
        _LOGGER.debug("Запрос принудительного обновления данных роутера Huawei")
        await self.coordinator.async_refresh()

    @property
    def device_info(self) -> DeviceInfo:
        """Связывание кнопки с карточкой роутера."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Роутер Huawei HS8545M",
            manufacturer="Huawei",
            model="HS8545M",
        )


class HuaweiRebootRouterButton(CoordinatorEntity, ButtonEntity):
    """Кнопка для перезагрузки роутера Huawei через Telnet."""

    _attr_has_entity_name = True
    _attr_translation_key = "reboot_router"  # Соответствует ключу в ru.json / en.json

    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry, client) -> None:
        """Инициализация."""
        super().__init__(coordinator)
        self._entry = entry
        self.client = client
        self._attr_unique_id = f"hw_btn_reboot_router_{entry.entry_id}"

    async def async_press(self) -> None:
        """Действие при нажатии кнопки: отправка команды перезагрузки по Telnet."""
        _LOGGER.warning("Инициирована перезагрузка роутера Huawei HS8545M")
        
        try:
            # Используем безопасный метод из __init__.py без дублирования логики подключения
            await self.client.execute_single_command("reboot")
            _LOGGER.info("Команда reboot успешно отправлена на роутер Huawei")
        except Exception as e:
            _LOGGER.error("Не удалось выполнить перезагрузку роутера по Telnet: %s", e)

    @property
    def device_info(self) -> DeviceInfo:
        """Связывание кнопки с карточкой роутера."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Роутер Huawei HS8545M",
            manufacturer="Huawei",
            model="HS8545M",
        )
