import re
import logging
from homeassistant.components.sensor import SensorEntity, SensorStateClass, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo

# Импортируем DOMAIN из __init__.py
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Регулярные выражения для парсинга текста ответов роутера
WAN_IP_REGEX = re.compile(r'TABLE_OF_IPV4IF\s*#####.*?Address\s+(?P<ip>(?:\d{1,3}\.){3}\d{1,3})', re.DOTALL | re.IGNORECASE)
CPU_REGEX = re.compile(r'CpuUsed\s*=\s*(?P<cpu>\d+)\s*Percent', re.IGNORECASE)
MEM_REGEX = re.compile(r'MemUsed\s*=\s*(?P<mem>\d+)\s*Percent', re.IGNORECASE)

# Регулярные выражения для Оптики (PON)
OPTIC_RX_REGEX = re.compile(r'RxPower\s*:\s*(?P<rx>[-]?\d+\.\d+)', re.IGNORECASE)
OPTIC_TX_REGEX = re.compile(r'TxPower\s*:\s*(?P<tx>[-]?\d+\.\d+)', re.IGNORECASE)
OPTIC_TEMP_REGEX = re.compile(r'Temperature\s*:\s*(?P<temp>\d+)', re.IGNORECASE)
OPTIC_VOLT_REGEX = re.compile(r'Voltage\s*:\s*(?P<volt>\d+)', re.IGNORECASE)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Настройка платформы сенсоров на основании записи конфигурации."""
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


class HuaweiBaseSensor(CoordinatorEntity, SensorEntity):
    """Базовый класс для всех сенсоров Huawei для исключения дублирования кода device_info."""
    
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry):
        """Инициализация базового сенсора."""
        super().__init__(coordinator)
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        """Связывание каждого сенсора с единым устройством роутера."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Роутер Huawei HS8545M",
            manufacturer="Huawei",
            model="HS8545M",
        )


class HuaweiWanIPSensor(HuaweiBaseSensor):
    """Сенсор внешнего IP-адреса роутера Huawei."""
    
    _attr_translation_key = "external_ip"
    _attr_icon = "mdi:earth"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"huawei_router_wan_ip_{entry.entry_id}"

    @property
    def native_value(self) -> str:
        if not self.coordinator.data: 
            return "Неизвестно"
        sys_data = self.coordinator.data.get("sys", "")
        match = WAN_IP_REGEX.search(sys_data)
        if match: 
            return match.group("ip")
        if "table_of_wan_ipv4_addr" in sys_data.lower():
            fallback = re.search(r'TABLE_OF_WAN_IPV4_ADDR\s*#####.*?Address\s+(?P<ip>(?:\d{1,3}\.){3}\d{1,3})', sys_data, re.DOTALL | re.IGNORECASE)
            if fallback: 
                return fallback.group("ip")
        return "Отключен"


class HuaweiCpuSensor(HuaweiBaseSensor):
    """Сенсор нагрузки на CPU."""
    
    _attr_translation_key = "cpu_load"
    _attr_icon = "mdi:cpu-64-bit"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"huawei_router_cpu_usage_{entry.entry_id}"

    @property
    def native_value(self) -> int:
        if not self.coordinator.data: 
            return 0
        match = CPU_REGEX.search(self.coordinator.data.get("sys", ""))
        return int(match.group("cpu")) if match else 0


class HuaweiMemorySensor(HuaweiBaseSensor):
    """Сенсор использования оперативной памяти."""
    
    _attr_translation_key = "memory_usage"
    _attr_icon = "mdi:memory"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"huawei_router_memory_usage_{entry.entry_id}"

    @property
    def native_value(self) -> int:
        if not self.coordinator.data: 
            return 0
        match = MEM_REGEX.search(self.coordinator.data.get("sys", ""))
        return int(match.group("mem")) if match else 0


class HuaweiOpticRxSensor(HuaweiBaseSensor):
    """Сенсор уровня оптического сигнала на прием (Rx)."""
    
    _attr_translation_key = "optic_rx_signal"
    _attr_icon = "mdi:import"
    _attr_native_unit_of_measurement = "dBm"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"huawei_router_optic_rx_{entry.entry_id}"

    @property
    def native_value(self) -> float:
        if not self.coordinator.data: 
            return 0.0
        match = OPTIC_RX_REGEX.search(self.coordinator.data.get("sys", ""))
        return float(match.group("rx")) if match else -40.0


class HuaweiOpticTxSensor(HuaweiBaseSensor):
    """Сенсор уровня оптического сигнала на передачу (Tx)."""
    
    _attr_translation_key = "optic_tx_power"
    _attr_icon = "mdi:export"
    _attr_native_unit_of_measurement = "dBm"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"huawei_router_optic_tx_{entry.entry_id}"

    @property
    def native_value(self) -> float:
        if not self.coordinator.data: 
            return 0.0
        match = OPTIC_TX_REGEX.search(self.coordinator.data.get("sys", ""))
        return float(match.group("tx")) if match else 0.0


class HuaweiOpticTempSensor(HuaweiBaseSensor):
    """Сенсор температуры оптического трансивера (лазера)."""
    
    _attr_translation_key = "optic_temperature"
    _attr_native_unit_of_measurement = "°C"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_device_class = SensorDeviceClass.TEMPERATURE

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"huawei_router_optic_temp_{entry.entry_id}"

    @property
    def native_value(self) -> int:
        if not self.coordinator.data: 
            return 0
        match = OPTIC_TEMP_REGEX.search(self.coordinator.data.get("sys", ""))
        return int(match.group("temp")) if match else 0


class HuaweiOpticVoltSensor(HuaweiBaseSensor):
    """Сенсор напряжения (вольтажа) оптического модуля."""
    
    _attr_translation_key = "optic_voltage"
    _attr_icon = "mdi:sine-wave"
    _attr_native_unit_of_measurement = "V"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_device_class = SensorDeviceClass.VOLTAGE

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"huawei_router_optic_volt_{entry.entry_id}"

    @property
    def native_value(self) -> float:
        if not self.coordinator.data: 
            return 0.0
        match = OPTIC_VOLT_REGEX.search(self.coordinator.data.get("sys", ""))
        # Напряжение из терминалов роутеров Huawei обычно возвращается в мВ (mV), 
        # переводим в Вольты (V) для красивого отображения, если это необходимо
        if match:
            mv_value = float(match.group("volt"))
            return round(mv_value / 1000.0, 2) if mv_value > 100 else mv_value
        return 0.0
