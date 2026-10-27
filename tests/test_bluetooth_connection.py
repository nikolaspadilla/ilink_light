"""Exercise the real connection boundary without a Bluetooth radio or HA install."""
import asyncio
import importlib
import logging
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import AsyncMock, Mock, patch


class FakeBleakError(Exception):
    pass


class FakeBleakClient:
    def __init__(self, device):
        self.device = device
        self.is_connected = False

    async def connect(self):
        logging.getLogger("habluetooth.wrappers").warning(
            "BleakClient.connect() called without bleak-retry-connector"
        )
        self.is_connected = True
        # Modern Bleak returns None on success.


def load_client():
    """Stub external boundaries; load the integration's real client and protocol."""
    package = types.ModuleType("ilink_connection_test")
    package.__path__ = [str(Path(__file__).parents[1] / "custom_components/ilink_light")]
    modules = {
        "ilink_connection_test": package,
        "bleak": types.ModuleType("bleak"),
        "bleak.exc": types.ModuleType("bleak.exc"),
        "bleak_retry_connector": types.ModuleType("bleak_retry_connector"),
        "home_assistant_bluetooth": types.ModuleType("home_assistant_bluetooth"),
        "homeassistant": types.ModuleType("homeassistant"),
        "homeassistant.const": types.ModuleType("homeassistant.const"),
        "homeassistant.components": types.ModuleType("homeassistant.components"),
        "homeassistant.components.bluetooth": types.ModuleType("homeassistant.components.bluetooth"),
    }
    modules["bleak"].BleakClient = FakeBleakClient
    modules["bleak"].BleakGATTCharacteristic = object
    modules["bleak"].BLEDevice = object
    modules["bleak.exc"].BleakError = FakeBleakError
    modules["bleak_retry_connector"].BleakClientWithServiceCache = FakeBleakClient
    modules["bleak_retry_connector"].establish_connection = AsyncMock()
    modules["home_assistant_bluetooth"].BluetoothServiceInfoBleak = object
    modules["homeassistant.const"].Platform = types.SimpleNamespace(LIGHT="light")
    modules["homeassistant.components"].bluetooth = modules["homeassistant.components.bluetooth"]
    with patch.dict(sys.modules, modules):
        return importlib.import_module("ilink_connection_test.light_bt_client")


client_module = load_client()


class ConnectionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.device = types.SimpleNamespace(address="AA:BB:CC:DD:EE:FF", name="Test light")
        self.connection = FakeBleakClient(self.device)
        self.connection.is_connected = True
        self.lookup = Mock(return_value=self.device)
        self.helper = AsyncMock(return_value=self.connection)
        self.client = client_module.LightBtClient(object(), self.device.address.lower())
        self.client._initialize = AsyncMock()
        self.patches = [
            patch.object(client_module.bluetooth, "async_ble_device_from_address", self.lookup, create=True),
            patch.object(client_module, "establish_connection", self.helper, create=True),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    async def test_connection_uses_helper_without_direct_connect_warning(self):
        with self.assertNoLogs("habluetooth.wrappers", level="WARNING"):
            self.assertTrue(await self.client.connect(retries=3))
        self.helper.assert_awaited_once()
        args, kwargs = self.helper.call_args
        self.assertIs(args[0], client_module.BleakClientWithServiceCache)
        self.assertIs(args[1], self.device)
        self.assertEqual(kwargs["max_attempts"], 3)
        self.lookup.assert_called_with(self.client._hass, self.device.address, connectable=True)

    async def test_connected_client_is_initialized_without_boolean_connect_result(self):
        self.assertTrue(await self.client.connect())
        self.client._initialize.assert_awaited_once()

    async def test_success_subscribes_and_requests_initial_status(self):
        self.client._initialize = client_module.LightBtClient._initialize.__get__(self.client)
        self.connection.start_notify = AsyncMock()
        self.client.request_status_update = AsyncMock()
        with patch.object(client_module.bluetooth, "async_last_service_info", return_value=None, create=True):
            self.assertTrue(await self.client.connect())
        self.connection.start_notify.assert_awaited_once_with(
            client_module.CHARACTERISTIC_REQUEST_STATUS, self.client._notification_handler
        )
        self.client.request_status_update.assert_awaited_once()

    async def test_disconnected_result_does_not_initialize(self):
        self.connection.is_connected = False
        self.assertFalse(await self.client.connect())
        self.client._initialize.assert_not_awaited()

    async def test_retry_callback_refreshes_connectable_device(self):
        await self.client.connect()
        callback = self.helper.call_args.kwargs["ble_device_callback"]
        replacement = types.SimpleNamespace(address=self.device.address, name="New route")
        self.lookup.return_value = replacement
        self.assertIs(callback(), replacement)

    async def test_exhausted_helper_does_not_initialize_or_leave_connecting(self):
        self.helper.side_effect = FakeBleakError("unreachable")
        self.assertFalse(await self.client.connect())
        self.helper.assert_awaited_once()
        self.client._initialize.assert_not_awaited()
        self.assertFalse(self.client._connecting)

    async def test_cancellation_clears_connecting_flag_and_propagates(self):
        self.helper.side_effect = asyncio.CancelledError
        with self.assertRaises(asyncio.CancelledError):
            await self.client.connect()
        self.assertFalse(self.client._connecting)

    async def test_reconnect_uses_helper_with_current_device(self):
        self.client._bt_client = FakeBleakClient(self.device)
        replacement = types.SimpleNamespace(address=self.device.address, name="New route")
        self.lookup.return_value = replacement
        self.assertTrue(await self.client.connect())
        self.assertIs(self.helper.call_args.args[1], replacement)

    async def test_existing_connection_is_not_replaced(self):
        self.client._bt_client = self.connection
        self.assertTrue(await self.client.connect())
        self.helper.assert_not_awaited()
        self.lookup.assert_not_called()

    async def test_missing_device_fails_without_helper(self):
        self.lookup.return_value = None
        self.assertFalse(await self.client.connect(retries=1))
        self.helper.assert_not_awaited()
        self.assertFalse(self.client._connecting)


if __name__ == "__main__":
    unittest.main()
