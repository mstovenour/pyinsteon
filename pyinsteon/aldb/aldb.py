"""Insteon All-Link Database.

The All-Link database contains database records that represent links to other
Insteon devices that either respond to or control the current device.
"""
import logging

from ..constants import ALDBStatus, ALDBVersion
from ..managers.aldb_read_manager import ALDBReadManager
from .aldb_base import ALDBBase

_LOGGER = logging.getLogger(__name__)


class ALDB(ALDBBase):
    """All-Link Database for a device."""

    def __init__(
        self,
        address,
        version=ALDBVersion.V2,
        mem_addr=0x0FFF,
    ):
        """Init the ALDB class."""
        super().__init__(address=address, version=version, mem_addr=mem_addr)
        self._read_manager = ALDBReadManager(self)

    # pylint: disable=arguments-differ
    async def async_load(
        self, mem_addr: int = 0x00, num_recs: int = 0x00, refresh: bool = False
    ):
        """Load the All-Link Database."""
        _LOGGER.debug("Loading the ALDB async")
        self._update_status(ALDBStatus.LOADING)
        if refresh:
            self.clear()
        else:
            # Pop any unused records to make sure we query them
            unused = list(self.find(in_use=False))
            for rec in unused:
                self._records.pop(rec.mem_addr)

        async for rec in self._read_manager.async_read(
            mem_addr=mem_addr, num_recs=num_recs
        ):
            _LOGGER.debug("Loading record: %s", str(rec))
            # Make sure the records make sense
            if (
                self.high_water_mark_mem_addr
                and rec.mem_addr < self.high_water_mark_mem_addr
            ):
                _LOGGER.debug("Record is after the HWM: %s", str(rec))
                continue

            # If an existing record will be replaced notify of change
            old_record = self._records.get(rec.mem_addr)

            # If the old rec is identical to the new rec, do nothing
            if old_record and rec.is_exact_match(old_record):
                _LOGGER.debug("Record has not changed:")
                _LOGGER.debug("Old: %s", str(old_record))
                _LOGGER.debug("New: %s", str(rec))
                continue

            if old_record and old_record.is_in_use:
                self._notify_change(self._records[rec.mem_addr], force_delete=True)

            self._records[rec.mem_addr] = rec
            self._notify_change(rec)

            if self._calc_load_status():
                break

        self.set_load_status()

        return self._status
