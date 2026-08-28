import logging
import telnetlib
import asyncio
import time
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)
DOMAIN = "huawei_wap_tracker"
PLATFORMS = ["device_tracker", "button", "sensor", "switch"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Настройка интеграции Huawei WAP Tracker из Config Entry."""
    config = entry.data

    def fetch_from_router():
        try:
            tn = telnetlib.Telnet(config["host"], 23, timeout=10)
            
            tn.read_until(b"Login:", timeout=3)
            tn.write(config["username"].encode('ascii') + b"\n")
            
            tn.read_until(b"Password:", timeout=3)
            tn.write(config["password"].encode('ascii') + b"\n")
            tn.read_until(b"WAP>", timeout=5)
            
            # Сбор 1: Использование процессора, памяти и системное время
            tn.write(b"display sysinfo\n")
            time.sleep(0.3)
            sys_text = tn.read_until(b"WAP>", timeout=4).decode('utf-8', errors='ignore')
            
            # Сбор 2: Подробные данные о WAN-интерфейсе для внешнего IP-адреса
            tn.write(b"display wan layer all\n")
            time.sleep(0.3)
            wan_text = tn.read_until(b"WAP>", timeout=4).decode('utf-8', errors='ignore')

            # ДОБАВЛЕНО: Сбор 3: Диагностика оптического сигнала PON линка
            tn.write(b"display optic\n")
            time.sleep(0.3)
            optic_text = tn.read_until(b"WAP>", timeout=4).decode('utf-8', errors='ignore')
            
            # Сбор 4: Общая таблица MAC-адресов коммутатора (LAN + Wi-Fi)
            tn.write(b"display macaddress\n")
            time.sleep(0.3)
            mac_text = tn.read_until(b"WAP>", timeout=4).decode('utf-8', errors='ignore')

            # Сбор 5: Таблица аренды DHCP для сопоставления MAC с Hostname
            tn.write(b"display dhcp server user all\n")
            time.sleep(0.3)
            dhcp_text = tn.read_until(b"WAP>", timeout=4).decode('utf-8', errors='ignore')
            
            tn.write(b"logout\n")
            tn.close()

            # Склеиваем системные, WAN и Оптические данные для платформы сенсоров
            combined_sys_text = sys_text + "\n" + wan_text + "\n" + optic_text
            combined_network_text = mac_text + "\n" + dhcp_text
            
            return {
                "sys": combined_sys_text, 
                "wifi": combined_network_text
            }
        except Exception as e:
            _LOGGER.error("Telnet communication error with Huawei Router: %s", e)
            raise UpdateFailed(f"Сбой связи Telnet: {e}")

    async def async_update_data():
        return await hass.async_add_executor_job(fetch_from_router)

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Huawei Router Data",
        update_method=async_update_data,
        update_interval=timedelta(seconds=30),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "config": config,
        "coordinator": coordinator
    }

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
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return True
