import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity

# Импортируем наш клиент и DOMAIN из __init__.py
from . import DOMAIN, HuaweiTelnetClient

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Настройка платформы switch из Config Entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([HuaweiLedSwitch(coordinator, entry)])


class HuaweiLedSwitch(CoordinatorEntity, RestoreEntity, SwitchEntity):
    """Выключатель режима индикации роутера Huawei."""

    # Включаем поддержку автоматического именования через переводы
    _attr_has_entity_name = True
    _attr_translation_key = "router_led"

    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Инициализация."""
        super().__init__(coordinator)
        self._config = entry.data
        self._entry = entry
        self._attr_unique_id = f"hw_led_diag_switch_{entry.entry_id}"
        self._is_on = False
        
        # Создаем экземпляр нашего асинхронного клиента для управления
        self._client = HuaweiTelnetClient(
            host=self._config["host"],
            username=self._config["username"],
            password=self._config["password"],
        )

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

    async def _async_send_command(self, command: str) -> bool:
        """Внутренний асинхронный метод для отправки команды управления на роутер."""
        try:
            # Вызываем fetch_data только для того, чтобы клиент выполнил коннект и логин, 
            # но так как в нашем клиенте fetch_data выполняет и сбор данных, и дисконнект, 
            # мы можем использовать точечную сессию внутри метода:
            await self._client.fetch_data()
            
            # Однако, для отправки единичной управляющей команды эффективнее открыть прямую сессию:
            import asyncio
            reader, writer = await asyncio.open_connection(self._config["host"], 23)
            
            # Быстрый логин (механика аналогична клиенту из __init__.py)
            buffer = b""
            while b"Login:" not in buffer:
                buffer += await asyncio.wait_for(reader.read(1024), timeout=3.0)
            writer.write(self._config["username"].encode("ascii") + b"\n")
            await writer.drain()
            
            buffer = b""
            while b"Password:" not in buffer:
                buffer += await asyncio.wait_for(reader.read(1024), timeout=3.0)
            writer.write(self._config["password"].encode("ascii") + b"\n")
            await writer.drain()
            
            # Ожидаем приглашение
            buffer = b""
            while b"WAP>" not in buffer:
                buffer += await asyncio.wait_for(reader.read(1024), timeout=4.0)
                
            # Отправляем команду переключения
            writer.write(f"{command}\n".encode("ascii"))
            await writer.drain()
            await asyncio.sleep(0.3)
            
            # Выход
            writer.write(b"logout\n")
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return True
        except Exception as e:
            _LOGGER.error("Ошибка асинхронного управления LED по Telnet: %s", e)
            return False

    async def async_turn_on(self, **kwargs) -> None:
        """Включение светодиодов (Асинхронная команда)."""
        success = await self._async_send_command("set led switch on")
        if success:
            self._is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Выключение светодиодов (Асинхронная команда)."""
        success = await self._async_send_command("set led switch off")
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
