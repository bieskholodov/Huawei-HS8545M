# custom_components/huawei_wap_tracker/switch.py

import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity

# Импортируем DOMAIN из __init__.py
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Настройка платформы switch из Config Entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    client = hass.data[DOMAIN][entry.entry_id]["client"]
    
    async_add_entities([HuaweiLedSwitch(coordinator, entry, client)])


class HuaweiLedSwitch(CoordinatorEntity, RestoreEntity, SwitchEntity):
    """Выключатель режима индикации роутера Huawei."""

    # Включаем поддержку автоматического именования через переводы
    _attr_has_entity_name = True
    _attr_translation_key = "diagnostic_mode"

    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry, client) -> None:
        """Инициализация."""
        super().__init__(coordinator)
        self._entry = entry
        self.client = client
        self._attr_unique_id = f"hw_led_diag_switch_{entry.entry_id}"
        self._is_on = False

    @property
    def icon(self) -> str:
        return "mdi:wrench-clock" if self._is_on else "mdi:router-wireless"

    @property
    def is_on(self) -> bool:
        """Возвращает текущее состояние выключателя."""
        return self._is_on

    async def async_added_to_hass(self) -> None:
        """Восстановление состояния тумблера после перезагрузки Home Assistant."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state:
            self._is_on = state.state == "on"

    async def async_turn_on(self, **kwargs) -> None:
        """Включение светодиодов через центральный асинхронный клиент."""
        try:
            # Выполняем точечную команду через безопасную сессию общего клиента
            await self.client.execute_single_command("set led switch on")
            self._is_on = True
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error("Ошибка переключения светодиодов роутера (on): %s", e)

    async def async_turn_off(self, **kwargs) -> None:
        """Выключение светодиодов через центральный асинхронный клиент."""
        try:
            # Выполняем точечную команду через безопасную сессию общего клиента
            await self.client.execute_single_command("set led switch off")
            self._is_on = False
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error("Ошибка переключения светодиодов роутера (off): %s", e)

    @property
    def device_info(self) -> DeviceInfo:
        """Связывание выключателя с общей карточкой роутера."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Роутер Huawei HS8545M",
            manufacturer="Huawei",
            model="HS8545M",
        )
