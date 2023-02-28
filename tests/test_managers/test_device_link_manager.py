"""Test the device_link_manager class."""
import asyncio
from random import randint
import unittest
from unittest.mock import AsyncMock, Mock

from pyinsteon import devices, link_manager
from pyinsteon.aldb.aldb_record import ALDBRecord
from pyinsteon.device_types.hub import Hub

from tests import load_devices, set_log_levels
from tests.utils import TopicItem, async_case, cmd_kwargs, send_topics


def _reset_devices(addresses):
    """Reset the device ALDB pending records."""
    for addr in addresses:
        device = devices[addr]
        device.async_status = AsyncMock()
        device.aldb.clear_pending()
        device.aldb.async_write = AsyncMock()
        device.aldb.async_write.call_count = 0
        device.aldb.clear = Mock()


def _add_rec_to_aldb(device, record):
    """Add a record to a device ALDB."""
    hwm = None
    for rec in device.aldb.find(target="000000"):
        hwm = rec
        break

    if record.mem_addr == 0:
        record.mem_addr = hwm.mem_addr
        hwm.mem_addr = hwm.mem_addr - 8
        records = {record.mem_addr: record, hwm.mem_addr: hwm}
    else:
        records = {record.mem_addr: record}
    device.aldb.load_saved_records(device.aldb.status, records)
    return record.mem_addr


# evices = DeviceManager()


# @pytest.fixture(autouse=True)
# def devices_fixture():
#     """Load the devices fixture."""
#     with patch.object(pyinsteon, "devices", devices):
#         yield


class TestDeviceLinkManager(unittest.TestCase):
    """Test the DeviceLinkManager class."""

    def setUp(self) -> None:
        """Set up the tests."""
        set_log_levels(logger_topics=True)

    @async_case
    async def test_device_links(self):
        """Test device links."""

        modem = Hub("111111", 0x03, 51, 165, "Instoen modem")
        devices.modem = modem
        # link_manager = DeviceLinkManager(devices)
        await load_devices(devices)
        await asyncio.sleep(1)
        _reset_devices(list(devices))
        assert len(link_manager.links) == 2

        topic = "1a1a1a.1.on.all_link_broadcast"
        topic_item = TopicItem(topic, cmd_kwargs(0x11, 0xFF, None, "00.00.01"), 0)
        send_topics([topic_item])
        await asyncio.sleep(2)
        assert devices["3c3c3c"].async_status.call_count == 1

        controller = devices["1a1a1a"].address
        responder = devices["3c3c3c"].address
        link_data = link_manager.links[controller][1][responder]
        assert link_data[0].data1 == 255
        assert link_data[0].data3 == 1

        # Test adding and removing links
        controller = devices["aaaaaa"].address
        responder_1 = devices["6f6f6f"].address
        responder_2 = devices["5e5e5e"].address
        controller_3 = devices["4d4d4d"].address

        group = randint(0, 255)
        c_rec = ALDBRecord(
            memory=0,
            controller=True,
            group=group,
            target=responder_1,
            data1=0,
            data2=0,
            data3=0,
            in_use=True,
        )
        c_del_rec = ALDBRecord(
            memory=0,
            controller=True,
            group=group,
            target=responder_1,
            data1=0,
            data2=0,
            data3=0,
            in_use=False,
        )
        r_rec = ALDBRecord(
            memory=0,
            controller=False,
            group=group,
            target=controller,
            data1=0,
            data2=0,
            data3=0,
            in_use=True,
        )
        r_del_rec = ALDBRecord(
            memory=0,
            controller=False,
            group=group,
            target=controller,
            data1=0,
            data2=0,
            data3=0,
            in_use=False,
        )
        r_3_rec = ALDBRecord(
            memory=0,
            controller=False,
            group=group,
            target=controller_3,
            data1=0,
            data2=0,
            data3=0,
            in_use=True,
        )

        # Create a controller record
        await asyncio.sleep(0.3)
        _reset_devices([controller])
        c_rec_mem_addr = _add_rec_to_aldb(devices[controller], c_rec)
        await asyncio.sleep(0.1)
        assert len(link_manager.links) == 3
        assert len(link_manager.links[controller]) == 1
        assert len(link_manager.links[controller][group]) == 1
        assert not link_manager.links[controller][group][responder_1]

        # Create corresponding responder record
        r_rec.mem_addr = 0
        resp_1_mem_addr = _add_rec_to_aldb(devices[responder_1], r_rec)
        await asyncio.sleep(0.1)
        assert len(link_manager.links) == 3
        assert len(link_manager.links[controller]) == 1
        assert len(link_manager.links[controller][group]) == 1
        assert len(link_manager.links[controller][group][responder_1]) == 1

        # Create second responder record
        r_rec.mem_addr = 0
        resp_2_mem_addr = _add_rec_to_aldb(devices[responder_2], r_rec)
        await asyncio.sleep(0.1)
        assert len(link_manager.links) == 3
        assert len(link_manager.links[controller]) == 1
        assert len(link_manager.links[controller][group]) == 2
        assert len(link_manager.links[controller][group][responder_1]) == 1
        assert len(link_manager.links[controller][group][responder_2]) == 1

        # Create new responder record with differnt controller
        _add_rec_to_aldb(devices[responder_2], r_3_rec)
        await asyncio.sleep(0.1)
        assert len(link_manager.links) == 4
        assert len(link_manager.links[controller_3]) == 1
        assert len(link_manager.links[controller_3][group]) == 1
        assert len(link_manager.links[controller_3][group][responder_2]) == 1

        # Remove responder 1 record
        r_del_rec.mem_addr = resp_1_mem_addr
        _add_rec_to_aldb(devices[responder_1], r_del_rec)
        await asyncio.sleep(0.1)
        # Responder 2 and controller for responder 1 records still exist
        assert len(link_manager.links) == 4
        assert len(link_manager.links[controller]) == 1
        assert len(link_manager.links[controller][group]) == 2

        # Remove responder 2 record
        r_del_rec.mem_addr = resp_2_mem_addr
        _add_rec_to_aldb(devices[responder_2], r_del_rec)
        await asyncio.sleep(0.1)
        # Controller record still exists
        assert len(link_manager.links) == 4
        assert len(link_manager.links[controller]) == 1
        assert len(link_manager.links[controller][group]) == 1

        # Remove the corresponding controller record
        c_del_rec.mem_addr = c_rec_mem_addr
        _add_rec_to_aldb(devices[controller], c_del_rec)
        await asyncio.sleep(0.1)
        assert len(link_manager.links) == 3
        assert not link_manager.links.get(controller)