# custom_components/huawei_wap_tracker/config_flow.py

import logging
from typing import Any
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResult

# Импортируем наш асинхронный клиент, DOMAIN и исключение InvalidAuth из __init__.py
from . import DOMAIN, HuaweiTelnetClient, InvalidAuth

_LOGGER = logging.getLogger(__name__)

class HuaweiWapConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Поток конфигурации для Huawei WAP Tracker."""
    
    VERSION = 1

    def __init__(self) -> None:
        """Инициализация потока конфигурации."""
        self._reauth_entry: config_entries.ConfigEntry | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
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
            except InvalidAuth as err:
                _LOGGER.warning("Ошибка аутентификации Telnet при настройке: %s", err)
                # Возвращаем ключ ошибки для неверных учетных данных
                errors["base"] = "invalid_auth"
            except Exception as err:
                _LOGGER.error("Ошибка валидации Telnet при настройке: %s", err)
                # Возвращаем ключ ошибки отсутствия связи
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

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        """Инициирует процесс повторной авторизации при смене пароля роутера."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Шаг подтверждения и ввода новых учетных данных для reauth."""
        errors = {}
        
        if user_input is not None:
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]
            host = self._reauth_entry.data[CONF_HOST] if self._reauth_entry else "192.168.100.1"

            try:
                # Проверяем новые учетные данные через одиночную тестовую команду
                client = HuaweiTelnetClient(host, username, password)
                await client.execute_single_command("display sysinfo")
                
                # При успехе обновляем данные, перезагружаем интеграцию и закрываем уведомление reauth
                return self.async_update_reload_and_abort(
                    self._reauth_entry,
                    data={
                        **self._reauth_entry.data,
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                    },
                )
            except InvalidAuth as err:
                _LOGGER.warning("Ошибка повторной аутентификации Telnet: %s", err)
                errors["base"] = "invalid_auth"
            except Exception as err:
                _LOGGER.error("Ошибка связи Telnet при повторной авторизации: %s", err)
                errors["base"] = "cannot_connect"

        current_username = self._reauth_entry.data.get(CONF_USERNAME, "root") if self._reauth_entry else "root"
        current_host = self._reauth_entry.data.get(CONF_HOST, "") if self._reauth_entry else ""

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({
                vol.Required(CONF_USERNAME, default=current_username): str,
                vol.Required(CONF_PASSWORD): str,
            }),
            errors=errors,
            description_placeholders={"host": current_host},
        )
