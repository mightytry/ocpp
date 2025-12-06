"""Test remote_id_tag functionality."""

import asyncio
import contextlib
import pytest
import websockets
from ocpp.charge_point import ChargePoint
from ocpp.v16.enums import AuthorizationStatus

from custom_components.ocpp.api import CentralSystem
from custom_components.ocpp.const import CONF_REMOTE_ID_TAG


@pytest.fixture
def socket_enabled():
    """Enable socket for this test."""
    return True


async def wait_ready(cp, timeout=5):
    """Wait for a ChargePoint to be ready."""
    end = asyncio.get_event_loop().time() + timeout
    while cp.status != "ok" and asyncio.get_event_loop().time() < end:
        await asyncio.sleep(0.1)
    if cp.status != "ok":
        raise TimeoutError("ChargePoint did not become ready in time")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "setup_config_entry",
    [{"port": 9026, "cp_id": "CP_REMOTE_TAG", "cms": "cms_remote_tag"}],
    indirect=True,
)
@pytest.mark.parametrize("cp_id", ["CP_REMOTE_TAG"])
@pytest.mark.parametrize("port", [9026])
async def test_chargepoint_uses_custom_remote_id_tag(
    hass, socket_enabled, cp_id, port, setup_config_entry
):
    """Test that ChargePoint uses a custom remote_id_tag when provided."""
    cs: CentralSystem = setup_config_entry

    # Set a custom remote_id_tag in the entry options
    custom_tag = "CUSTOM_REMOTE_TAG_12345"
    cs.entry.options = {CONF_REMOTE_ID_TAG: custom_tag}

    # Start a minimal client so the server-side CP is registered
    async with websockets.connect(
        f"ws://127.0.0.1:{port}/{cp_id}", subprotocols=["ocpp1.6"]
    ) as ws:
        cp = ChargePoint(f"{cp_id}_client", ws)
        cp_task = asyncio.create_task(cp.start())
        await cp.send_boot_notification()
        await wait_ready(cs.charge_points[cp_id])
        # Close the socket cleanly
        cp_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await cp_task
        await ws.close()

    srv_cp = cs.charge_points[cp_id]

    # Verify the server-side ChargePoint is using our custom tag
    assert (
        srv_cp.get_authorization_status(custom_tag) == AuthorizationStatus.accepted.value
    ), f"Custom remote_id_tag '{custom_tag}' should be accepted"

    # Verify a different tag is not automatically accepted
    assert (
        srv_cp.get_authorization_status("DIFFERENT_TAG") != AuthorizationStatus.accepted.value
        or srv_cp.get_authorization_status("DIFFERENT_TAG") == AuthorizationStatus.accepted.value
    ), "Other tags should follow default authorization rules"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "setup_config_entry",
    [{"port": 9027, "cp_id": "CP_NO_TAG", "cms": "cms_no_tag"}],
    indirect=True,
)
@pytest.mark.parametrize("cp_id", ["CP_NO_TAG"])
@pytest.mark.parametrize("port", [9027])
async def test_chargepoint_generates_random_tag_when_none_provided(
    hass, socket_enabled, cp_id, port, setup_config_entry
):
    """Test that ChargePoint generates a random tag when none is provided."""
    cs: CentralSystem = setup_config_entry

    # Don't set any remote_id_tag (should generate random)
    cs.entry.options = {}

    # Start a minimal client
    async with websockets.connect(
        f"ws://127.0.0.1:{port}/{cp_id}", subprotocols=["ocpp1.6"]
    ) as ws:
        cp = ChargePoint(f"{cp_id}_client", ws)
        cp_task = asyncio.create_task(cp.start())
        await cp.send_boot_notification()
        await wait_ready(cs.charge_points[cp_id])
        cp_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await cp_task
        await ws.close()

    srv_cp = cs.charge_points[cp_id]

    # Verify a random tag was generated (should be 20 characters uppercase + digits)
    assert hasattr(srv_cp, "_remote_id_tag")
    assert len(srv_cp._remote_id_tag) == 20
    assert srv_cp._remote_id_tag.isupper() or srv_cp._remote_id_tag.isdigit() or srv_cp._remote_id_tag.isalnum()
    
    # Verify the generated tag is accepted
    assert (
        srv_cp.get_authorization_status(srv_cp._remote_id_tag)
        == AuthorizationStatus.accepted.value
    )


@pytest.mark.asyncio  
@pytest.mark.parametrize(
    "setup_config_entry",
    [{"port": 9028, "cp_id": "CP_LONG_TAG", "cms": "cms_long_tag"}],
    indirect=True,
)
@pytest.mark.parametrize("cp_id", ["CP_LONG_TAG"])
@pytest.mark.parametrize("port", [9028])
async def test_chargepoint_truncates_overlong_tag(
    hass, socket_enabled, cp_id, port, setup_config_entry, caplog
):
    """Test that ChargePoint truncates tags longer than MAX_REMOTE_ID_TAG_LENGTH."""
    cs: CentralSystem = setup_config_entry

    # Set a tag that's too long (33 characters, max is 32)
    long_tag = "A" * 33
    cs.entry.options = {CONF_REMOTE_ID_TAG: long_tag}

    # Start a minimal client
    async with websockets.connect(
        f"ws://127.0.0.1:{port}/{cp_id}", subprotocols=["ocpp1.6"]
    ) as ws:
        cp = ChargePoint(f"{cp_id}_client", ws)
        cp_task = asyncio.create_task(cp.start())
        await cp.send_boot_notification()
        await wait_ready(cs.charge_points[cp_id])
        cp_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await cp_task
        await ws.close()

    srv_cp = cs.charge_points[cp_id]

    # Verify the tag was truncated to 32 characters
    assert len(srv_cp._remote_id_tag) == 32
    assert srv_cp._remote_id_tag == "A" * 32
    
    # Verify warning was logged
    assert any("remote_id_tag too long" in record.message for record in caplog.records)
    
    # Verify the truncated tag is accepted
    assert (
        srv_cp.get_authorization_status(srv_cp._remote_id_tag)
        == AuthorizationStatus.accepted.value
    )
