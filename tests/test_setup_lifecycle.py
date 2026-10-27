"""Test the real setup function against controlled Home Assistant boundaries."""
import asyncio
import importlib.util
import logging
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import AsyncMock, Mock, patch


def load_integration():
    package = "ilink_setup_test"
    names = ["homeassistant", "homeassistant.config_entries", "homeassistant.const",
             "homeassistant.core", "homeassistant.helpers",
             "homeassistant.helpers.device_registry", "homeassistant.helpers.entity_registry",
             package + ".const", package + ".coordinator"]
    modules = {name: types.ModuleType(name) for name in names}
    modules["homeassistant.config_entries"].ConfigEntry = object
    modules["homeassistant.core"].HomeAssistant = object
    modules["homeassistant.const"].CONF_DEVICES = "devices"
    modules["homeassistant.helpers.device_registry"].DeviceEntry = object
    const = modules[package + ".const"]
    const.LOGGER = logging.getLogger(package)
    const.CONF_MAC, const.CONF_NAME = "mac", "name"
    const.DOMAIN, const.PLATFORMS = "ilink_light", ["light"]
    modules[package + ".coordinator"].LightCoordinator = Mock()
    path = Path(__file__).parents[1] / "custom_components/ilink_light/__init__.py"
    spec = importlib.util.spec_from_file_location(package, path, submodule_search_locations=[str(path.parent)])
    module = importlib.util.module_from_spec(spec)
    modules[package] = module
    with patch.dict(sys.modules, modules):
        spec.loader.exec_module(module)
    return module


integration = load_integration()


class SetupLifecycleTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.background_tasks = []
        self.hass = types.SimpleNamespace(data={}, config_entries=types.SimpleNamespace())
        def schedule(coro):
            task = asyncio.create_task(coro)
            self.background_tasks.append(task)
            return task
        self.hass.async_create_task = schedule
        self.entry = types.SimpleNamespace(
            entry_id="existing-entry", data={"devices": {}},
            async_on_unload=Mock(), add_update_listener=Mock(return_value="remove-listener"),
        )

    async def drain_background_tasks(self):
        await asyncio.gather(*self.background_tasks, return_exceptions=True)

    async def test_setup_waits_for_platform_before_returning_or_registering_listener(self):
        entered, release = asyncio.Event(), asyncio.Event()
        async def forward(entry, platforms):
            entered.set()
            await release.wait()
        self.hass.config_entries.async_forward_entry_setups = AsyncMock(side_effect=forward)
        task = asyncio.create_task(integration.async_setup_entry(self.hass, self.entry))
        await entered.wait()
        try:
            self.assertFalse(task.done(), "setup returned before the light platform finished")
            self.entry.async_on_unload.assert_not_called()
        finally:
            release.set()
            await task
            await self.drain_background_tasks()
        self.assertEqual(self.background_tasks, [])
        self.entry.async_on_unload.assert_called_once_with("remove-listener")

    async def test_platform_failure_propagates_instead_of_reporting_success(self):
        self.hass.config_entries.async_forward_entry_setups = AsyncMock(side_effect=RuntimeError("platform failure"))
        try:
            with self.assertRaisesRegex(RuntimeError, "platform failure"):
                await integration.async_setup_entry(self.hass, self.entry)
        finally:
            await self.drain_background_tasks()
        self.entry.async_on_unload.assert_not_called()

    async def test_success_preserves_existing_device_identity_and_coordinator(self):
        self.hass.config_entries.async_forward_entry_setups = AsyncMock()
        self.entry.data = {"devices": {"existing-address": {"mac": "existing-address", "name": "Porch Light"}}}
        registry = types.SimpleNamespace(async_get_or_create=Mock(return_value=types.SimpleNamespace(id="existing-device")))
        coordinator = object()
        with patch.object(integration.dr, "async_get", return_value=registry, create=True), \
                patch.object(integration, "LightCoordinator", return_value=coordinator):
            self.assertTrue(await integration.async_setup_entry(self.hass, self.entry))
            await self.drain_background_tasks()
        registry.async_get_or_create.assert_called_once_with(
            config_entry_id="existing-entry", identifiers={("ilink_light", "existing-address")}, name="Porch Light"
        )
        self.assertIs(self.hass.data["ilink_light"]["devices"]["existing-address"], coordinator)
        self.hass.config_entries.async_forward_entry_setups.assert_awaited_once_with(self.entry, ["light"])
        self.assertEqual(self.background_tasks, [])


if __name__ == "__main__":
    unittest.main()
