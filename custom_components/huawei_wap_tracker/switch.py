import logging
import telnetlib
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity

_LOGGER = logging.getLogger(__name__)
DOMAIN = "huawei_wap_tracker"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Настройка платформы switch из Config Entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([HuaweiLedSwitch(coordinator, entry)])


class HuaweiLedSwitch(CoordinatorEntity, RestoreEntity, SwitchEntity):
    """Выключатель режима индикации роутера Huawei."""

    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Инициализация."""
        super().__init__(coordinator)
        self._config = entry.data
        self._entry = entry
        self._attr_name = "Huawei Роутер - Режим диагностики (Красный LED)"
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

    def _send_telnet_command(self, command: bytes) -> bool:
        """Отправка команды переключения светодиодов через Telnet."""
        try:
            tn = telnetlib.Telnet(self._config["host"], 23, timeout=5)
            tn.read_until(b"Login:", timeout=3)
            tn.write(self._config["username"].encode('ascii') + b"\n")
            tn.read_until(b"Password:", timeout=3)
            tn.write(self._config["password"].encode('ascii') + b"\n")
            tn.read_until(b"WAP>", timeout=3)
            
            # Отправляем команду
            tn.write(command)
            tn.read_until(b"WAP>", timeout=3)
            
            # Корректно закрываем сессию на роутере
            tn.write(b"logout\n")
            tn.close()
            return True
        except Exception as e:
            _LOGGER.error("Ошибка управления LED по Telnet: %s", e)
            return False

    async def async_turn_on(self, **kwargs) -> None:
        """Включение светодиодов (Ваша исходная рабочая команда)."""
        success = await self.hass.async_add_executor_job(
            self._send_telnet_command, b"set led switch on\n"
        )
        if success:
            self._is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Выключение светодиодов (Ваша исходная рабочая команда)."""
        success = await self.hass.async_add_executor_job(
            self._send_telnet_command, b"set led switch off\n"
        )
        if success:
            self._is_on = False
            self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        """Связывание выключателя с общей карточкой роутера."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Роутер Huawei HS8545M",
            manufacturer="Huawei",
            model="HS8545M",
        )

