import re
import logging
from datetime import datetime, timedelta
from homeassistant.core import callback, HomeAssistant
from homeassistant.components.device_tracker import ScannerEntity, SourceType
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.helpers.device_registry import DeviceInfo

_LOGGER = logging.getLogger(__name__)
DOMAIN = "huawei_wap_tracker"

# Время удержания статуса "Дома" (в секундах) для засыпающих Wi-Fi устройств
CONSIDER_HOME = 180 

# Регулярное выражение для поиска MAC-адресов в тексте
MAC_REGEX = re.compile(r'(?:[0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}|[0-9a-fA-F]{12}')

# Строгое регулярное выражение для DHCP таблицы
DHCP_REGEX = re.compile(
    r'(?:\d{1,3}\.){3}\d{1,3}\s+(?P<name>\S+)\s+(?P<mac>(?:[0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2})'
)


def normalize_mac(mac_str: str) -> str:
    """Приводит MAC к стандартному нижнему регистру с двоеточиями."""
    clean = mac_str.replace(":", "").replace("-", "").lower()
    return ":".join(clean[i:i+2] for i in range(0, 12, 2))

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Настройка платформы device_tracker со 100% динамическими именами."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    tracked_devices = {}

    @callback
    def parse_and_add() -> None:
        if not coordinator.data:
            return

        raw_output = coordinator.data.get("wifi", "")
        if not raw_output:
            return

        # Извлекаем абсолютно все активные MAC-адреса из таблиц коммутатора и DHCP
        raw_macs = MAC_REGEX.findall(raw_output)
        current_active_macs = {normalize_mac(mac) for mac in raw_macs}

        new_entities = []
        for mac in current_active_macs:
            if mac not in tracked_devices:
                # Начальное имя при создании сущности (если в DHCP пусто, пишем полный MAC)
                entity = HuaweiRouterDevice(coordinator, mac, entry)
                tracked_devices[mac] = entity
                new_entities.append(entity)
        
        if new_entities:
            async_add_entities(new_entities)

    entry.async_on_unload(coordinator.async_add_listener(parse_and_add))
    parse_and_add()


class HuaweiRouterDevice(CoordinatorEntity, ScannerEntity):
    """Динамическая сущность сетевого клиента роутера Huawei."""

    def __init__(self, coordinator: DataUpdateCoordinator, mac: str, entry: ConfigEntry) -> None:
        """Инициализация."""
        super().__init__(coordinator)
        self._mac = mac
        self._attr_unique_id = f"huawei_tracker_{mac}"
        self._entry = entry
        self._last_seen = None

    @property
    def name(self) -> str:
        """Динамически обновляет имя устройства прямо из текущих данных DHCP."""
        if not self.coordinator.data:
            return f"Устройство {self._mac.upper()}"

        raw_output = self.coordinator.data.get("wifi", "")
        
        # Сканируем DHCP таблицу в поисках имени именно для ЭТОГО MAC-адреса
        for match in DHCP_REGEX.finditer(raw_output):
            if normalize_mac(match.group("mac")) == self._mac:
                name = match.group("name").strip()
                if name and name != "--":
                    return name

        # Если имени в DHCP нет, возвращаем полный MAC заглавными буквами
        return f"Устройство {self._mac.upper()}"

    @property
    def source_type(self) -> SourceType:
        return SourceType.ROUTER

    @property
    def mac_address(self) -> str:
        return self._mac

    @property
    def is_connected(self) -> bool:
        """Проверка активности в объединенных таблицах роутера с фильтром засыпания."""
        if not self.coordinator.data:
            return False
        
        raw_output = self.coordinator.data.get("wifi", "")
        raw_macs = MAC_REGEX.findall(raw_output)
        active_macs = {normalize_mac(mac) for mac in raw_macs}
        
        if self._mac in active_macs:
            self._last_seen = datetime.now()
            return True
            
        if self._last_seen and (datetime.now() - self._last_seen) < timedelta(seconds=CONSIDER_HOME):
            return True
            
        return False

    @property
    def device_info(self) -> DeviceInfo:
        """Связывание динамического трекера с общей карточкой роутера."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Роутер Huawei HS8545M",
            manufacturer="Huawei",
            model="HS8545M",
        )
