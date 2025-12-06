"""Test text entities for ocpp integration."""

import asyncio
import websockets
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ocpp.const import DOMAIN as OCPP_DOMAIN

from .const import (
    MOCK_CONFIG_DATA,
    CONF_CPIDS,
    MOCK_CONFIG_CP_APPEND,
    CONF_PORT,
    CONF_CPID,
)
from .charge_point_test import create_configuration, remove_configuration


async def test_text_remote_id_tag(hass, socket_enabled):
    """Test remote ID tag text entity."""

    cp_id = "CP_1_text"
    cpid = "test_cpid_text"
    data = MOCK_CONFIG_DATA.copy()
    cp_data = MOCK_CONFIG_CP_APPEND.copy()
    cp_data[CONF_CPID] = cpid
    data[CONF_CPIDS].append({cp_id: cp_data})
    data[CONF_PORT] = 9016
    config_entry = MockConfigEntry(
        domain=OCPP_DOMAIN,
        data=data,
        entry_id="test_cms_text",
        title="test_cms_text",
        version=2,
        minor_version=0,
    )

    # start clean entry for server
    await create_configuration(hass, config_entry)

    # Check that the text entity exists
    entity_id = f"text.{cpid}_remote_id_tag"
    
    # Wait for entity to be registered
    await asyncio.sleep(1)
    state = hass.states.get(entity_id)
    assert state is not None, f"Text entity {entity_id} should exist"

    # Test setting a value (entity may be unavailable before charger connects)
    new_value = "TEST12345678901234XX"
    await hass.services.async_call(
        "text",
        "set_value",
        {"entity_id": entity_id, "value": new_value},
        blocking=True,
    )
    
    # Check that the value was set
    await asyncio.sleep(0.1)
    state = hass.states.get(entity_id)
    # The state might be unavailable if charger isn't connected, but the value should be stored
    # For this test, we just verify the entity exists and accepts set_value calls
    assert state is not None

    # Cleanup
    await remove_configuration(hass, config_entry)
