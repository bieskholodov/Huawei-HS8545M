import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD
import telnetlib

DOMAIN = "huawei_wap_tracker"

class HuaweiWapConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                def check_telnet():
                    tn = telnetlib.Telnet(user_input[CONF_HOST], 23, timeout=3)
                    tn.close()
                await self.hass.async_add_executor_job(check_telnet)
                return self.async_create_entry(title=user_input[CONF_HOST], data=user_input)
            except Exception:
                errors["base"] = "cannot_connect"

        DATA_SCHEMA = vol.Schema({
            vol.Required(CONF_HOST, default="192.168.100.1"): str,
            vol.Required(CONF_USERNAME, default="root"): str,
            vol.Required(CONF_PASSWORD): str,
        })

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=errors)
