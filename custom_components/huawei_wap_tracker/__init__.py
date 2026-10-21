import logging
import asyncio
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)
DOMAIN = "huawei_wap_tracker"
PLATFORMS = ["device_tracker", "button", "sensor", "switch"]

class HuaweiTelnetClient:
    """Асинхронный клиент для сбора данных с роутера Huawei."""

    def __init__(self, host: str, username: str, password: str):
        self.host = host
        self.username = username
        self.password = password
        self.reader = None
        self.writer = None

    async def _read_until(self, expected: bytes, timeout: float = 4.0) -> bytes:
        """Вспомогательный метод для чтения буфера до ожидаемой строки."""
        buffer = b""
        try:
            while expected not in buffer:
                data = await asyncio.wait_for(self.reader.read(1024), timeout=timeout)
                if not data:
                    break
                buffer += data
        except asyncio.TimeoutError:
            _LOGGER.debug("Таймаут ожидания строки %s. Текущий буфер: %s", expected, buffer)
        return buffer

    async def _send_command(self, command: str, timeout: float = 4.0) -> str:
        """Отправка команды в терминал и чтение ответа до приглашения командной строки."""
        if not self.writer:
            return ""
        self.writer.write(command.encode("ascii") + b"\n")
        await self.writer.drain()
        await asyncio.sleep(0.3)  # Замена старого time.sleep(0.3)
        
        data = await self._read_until(b"WAP>", timeout=timeout)
        return data.decode("utf-8", errors="ignore")

    async def fetch_data(self) -> dict:
        """Установка соединения и последовательный сбор всех метрик."""
        try:
            # Открытие асинхронного соединения
            self.reader, self.writer = await asyncio.open_connection(self.host, 23)
            
            # Авторизация: Логин
            await self._read_until(b"Login:", timeout=3.0)
            self.writer.write(self.username.encode("ascii") + b"\n")
            await self.writer.drain()
            
            # Авторизация: Пароль
            await self._read_until(b"Password:", timeout=3.0)
            self.writer.write(self.password.encode("ascii") + b"\n")
            await self.writer.drain()
            
            # Ожидаем базовое приглашение командной строки после успешного входа
            await self._read_until(b"WAP>", timeout=5.0)
            
            # Сбор 1: Использование процессора, памяти и системное время
            sys_text = await self._send_command("display sysinfo")
            
            # Сбор 2: Подробные данные о WAN-интерфейсе
            wan_text = await self._send_command("display wan layer all")

            # Сбор 3: Диагностика оптического сигнала PON линка
            optic_text = await self._send_command("display optic")
            
            # Сбор 4: Общая таблица MAC-адресов коммутатора
            mac_text = await self._send_command("display macaddress")

            # Сбор 5: Таблица аренды DHCP
            dhcp_text = await self._send_command("display dhcp server user all")
            
            # Корректное закрытие сессии роутера
            self.writer.write(b"logout\n")
            await self.writer.drain()
            
        except Exception as e:
            _LOGGER.error("Telnet communication error with Huawei Router at %s: %s", self.host, e)
            raise UpdateFailed(f"Сбой связи Telnet: {e}")
        finally:
            if self.writer:
                self.writer.close()
                await self.writer.wait_closed()
                self.writer = None
                self.reader = None

        # Формирование комбинированных строк для совместимости с сенсорами
        combined_sys_text = f"{sys_text}\n{wan_text}\n{optic_text}"
        combined_network_text = f"{mac_text}\n{dhcp_text}"
        
        return {
            "sys": combined_sys_text, 
            "wifi": combined_network_text
        }


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Настройка интеграции Huawei WAP Tracker из Config Entry."""
    config = entry.data
    client = HuaweiTelnetClient(config["host"], config["username"], config["password"])

    async def async_update_data():
        """Асинхронный метод обновления данных координатора."""
        return await client.fetch_data()

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Huawei Router Data",
        update_method=async_update_data,
        update_interval=timedelta(seconds=30),
    )

    # Первый запуск сбора данных при старте
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "config": config,
        "coordinator": coordinator
    }

    # Регистрация устройства в Device Registry Home Assistant
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name="Роутер Huawei HS8545M",
        manufacturer="Huawei",
        model="HS8545M",
    )
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Выгрузка интеграции и платформ."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return True
