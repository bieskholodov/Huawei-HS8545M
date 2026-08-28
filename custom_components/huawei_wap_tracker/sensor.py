import re
import logging
from homeassistant.components.sensor import SensorEntity, SensorStateClass, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.helpers.device_registry import DeviceInfo

_LOGGER = logging.getLogger(__name__)
DOMAIN = "huawei_wap_tracker"

# Регулярные выражения
WAN_IP_REGEX = re.compile(r'TABLE_OF_IPV4IF\s*#####.*?Address\s+(?P<ip>(?:\d{1,3}\.){3}\d{1,3})', re.DOTALL | re.IGNORECASE)
CPU_REGEX = re.compile(r'CpuUsed\s*=\s*(?P<cpu>\d+)\s*Percent', re.IGNORECASE)
MEM_REGEX = re.compile(r'MemUsed\s*=\s*(?P<mem>\d+)\s*Percent', re.IGNORECASE)

# Регулярные выражения для Оптики (PON)
OPTIC_RX_REGEX = re.compile(r'RxPower\s*:\s*(?P<rx>[-]?\d+\.\d+)', re.IGNORECASE)
OPTIC_TX_REGEX = re.compile(r'TxPower\s*:\s*(?P<tx>[-]?\d+\.\d+)', re.IGNORECASE)
OPTIC_TEMP_REGEX = re.compile(r'Temperature\s*:\s*(?P<temp>\d+)', re.IGNORECASE)
OPTIC_VOLT_REGEX = re.compile(r'Voltage\s*:\s*(?P<volt>\d+)', re.IGNORECASE)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Настройка платформы сенсоров."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    async_add_entities([
        HuaweiWanIPSensor(coordinator, entry),
        HuaweiCpuSensor(coordinator, entry),
        HuaweiMemorySensor(coordinator, entry),
        HuaweiOpticRxSensor(coordinator, entry),
        HuaweiOpticTxSensor(coordinator, entry),
        HuaweiOpticTempSensor(coordinator, entry),
        HuaweiOpticVoltSensor(coordinator, entry),
    ])


class HuaweiWanIPSensor(CoordinatorEntity, SensorEntity):
    """Сенсор внешнего IP-адреса роутера Huawei."""
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = "Huawei Роутер - Внешний IP"
        self._attr_unique_id = f"huawei_router_wan_ip_{entry.entry_id}"
        self._attr_icon = "mdi:earth"

    @property
    def native_value(self) -> str:
        if not self.coordinator.data: return "Неизвестно"
        sys_data = self.coordinator.data.get("sys", "")
        match = WAN_IP_REGEX.search(sys_data)
        if match: return match.group("ip")
        if "table_of_wan_ipv4_addr" in sys_data.lower():
            fallback = re.search(r'TABLE_OF_WAN_IPV4_ADDR\s*#####.*?Address\s+(?P<ip>(?:\d{1,3}\.){3}\d{1,3})', sys_data, re.DOTALL | re.IGNORECASE)
            if fallback: return fallback.group("ip")
        return "Отключен"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self._entry.entry_id)}, name="Роутер Huawei HS8545M", manufacturer="Huawei", model="HS8545M")


class HuaweiCpuSensor(CoordinatorEntity, SensorEntity):
    """Сенсор нагрузки на CPU."""
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = "Huawei Роутер - Нагрузка CPU"
        self._attr_unique_id = f"huawei_router_cpu_usage_{entry.entry_id}"
        self._attr_icon = "mdi:cpu-64-bit"
        self._attr_native_unit_of_measurement = "%"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int:
        if not self.coordinator.data: return 0
        match = CPU_REGEX.search(self.coordinator.data.get("sys", ""))
        return int(match.group("cpu")) if match else 0

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self._entry.entry_id)}, name="Роутер Huawei HS8545M", manufacturer="Huawei", model="HS8545M")


class HuaweiMemorySensor(CoordinatorEntity, SensorEntity):
    """Сенсор использования оперативной памяти."""
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = "Huawei Роутер - Использование памяти"
        self._attr_unique_id = f"huawei_router_memory_usage_{entry.entry_id}"
        self._attr_icon = "mdi:memory"
        self._attr_native_unit_of_measurement = "%"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int:
        if not self.coordinator.data: return 0
        match = MEM_REGEX.search(self.coordinator.data.get("sys", ""))
        return int(match.group("mem")) if match else 0

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self._entry.entry_id)}, name="Роутер Huawei HS8545M", manufacturer="Huawei", model="HS8545M")


class HuaweiOpticRxSensor(CoordinatorEntity, SensorEntity):
    """Сенсор уровня оптического сигнала на прием (Rx)."""
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = "Huawei Роутер - Оптика Rx Сигнал"
        self._attr_unique_id = f"huawei_router_optic_rx_{entry.entry_id}"
        self._attr_icon = "mdi:import"
        self._attr_native_unit_of_measurement = "dBm"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH

    @property
    def native_value(self) -> float:
        if not self.coordinator.data: return 0.0
        match = OPTIC_RX_REGEX.search(self.coordinator.data.get("sys", ""))
        return float(match.group("rx")) if match else -40.0 # -40dBm означает отсутствие сигнала

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self._entry.entry_id)}, name="Роутер Huawei HS8545M", manufacturer="Huawei", model="HS8545M")


class HuaweiOpticTxSensor(CoordinatorEntity, SensorEntity):
    """Сенсор уровня оптического сигнала на передачу (Tx)."""
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = "Huawei Роутер - Оптика Tx Мощность"
        self._attr_unique_id = f"huawei_router_optic_tx_{entry.entry_id}"
        self._attr_icon = "mdi:export"
        self._attr_native_unit_of_measurement = "dBm"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH

    @property
    def native_value(self) -> float:
        if not self.coordinator.data: return 0.0
        match = OPTIC_TX_REGEX.search(self.coordinator.data.get("sys", ""))
        return float(match.group("tx")) if match else 0.0

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self._entry.entry_id)}, name="Роутер Huawei HS8545M", manufacturer="Huawei", model="HS8545M")


class HuaweiOpticTempSensor(CoordinatorEntity, SensorEntity):
    """Сенсор температуры оптического трансивера (лазера)."""
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = "Huawei Роутер - Оптика Температура"
        self._attr_unique_id = f"huawei_router_optic_temp_{entry.entry_id}"
        self._attr_native_unit_of_measurement = "°C"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_class = SensorDeviceClass.TEMPERATURE

    @property
    def native_value(self) -> int:
        if not self.coordinator.data: return 0
        match = OPTIC_TEMP_REGEX.search(self.coordinator.data.get("sys", ""))
        return int(match.group("temp")) if match else 0

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self._entry.entry_id)}, name="Роутер Huawei HS8545M", manufacturer="Huawei", model="HS8545M")


class HuaweiOpticVoltSensor(CoordinatorEntity, SensorEntity):
    """Сенсор вольтажа оптического модуля."""
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = "Huawei Роутер - Оптика Вольтаж"
        self._attr_unique_id = f"huawei_router_optic_volt_{entry.entry_id}"
        self._attr_native_unit_of_measurement = "V"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_class = SensorDeviceClass.VOLTAGE

    @property
    def native_value(self) -> float:
        if not self.coordinator.data: return 0.0
        match = OPTIC_VOLT_REGEX.search(self.coordinator.data.get("sys", ""))
        # Превращаем милливольты (mV) в обычные Вольты (V), деля на 1000
        return round(int(match.group("volt")) / 1000.0, 2) if match else 0.0

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self._entry.entry_id)}, name="Роутер Huawei HS8545M", manufacturer="Huawei", model="HS8545M")
