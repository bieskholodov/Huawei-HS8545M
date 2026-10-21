import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD

# Импортируем наш асинхронный клиент и DOMAIN из __init__.py
from . import DOMAIN, HuaweiTelnetClient

_LOGGER = logging.getLogger(__name__)

class HuaweiWapConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Поток конфигурации для Huawei WAP Tracker."""
    
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Первый шаг настройки пользователем через интерфейс."""
        errors = {}

        if user_input is not None:
            # Инициализируем клиент с данными пользователя
            client = HuaweiTelnetClient(
                host=user_input[CONF_HOST],
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
            )
            
            try:
                # Пытаемся выполнить асинхронный сбор данных для проверки подключения
                await client.fetch_data()
                
                # Если сбор прошел успешно, создаем запись интеграции
                return self.async_create_entry(
                    title=user_input[CONF_HOST], 
                    data=user_input
                )
            except Exception as err:
                _LOGGER.error("Ошибка валидации Telnet при настройке: %s", err)
                # Возвращаем ключ ошибки, который будет переведен через en.json/ru.json
                errors["base"] = "cannot_connect"

        # Схема формы ввода (строки теперь будут локализованы через translation_key)
        DATA_SCHEMA = vol.Schema({
            vol.Required(CONF_HOST, default="192.168.100.1"): str,
            vol.Required(CONF_USERNAME, default="root"): str,
            vol.Required(CONF_PASSWORD): str,
        })

        return self.async_show_form(
            step_id="user", 
            data_schema=DATA_SCHEMA, 
            errors=errors
        )
