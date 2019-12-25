"""Manage outbound ON All-Link Cleanup ACK response to a device."""

from .all_link_cleanup_ack_command import AllLinkCleanupAckCommandHandlerBase
from ...topics import ON


class OnAllLinkCleanupAckCommand(AllLinkCleanupAckCommandHandlerBase):
    """Manage outbound ON All-Link Cleanup ACK command to a device."""

    def __init__(self, address, group):
        """Init the OnLevelCommand class."""
        super().__init__(topic=ON, address=address, group=group)

    # pylint: disable=arguments-differ, useless-super-delegation
    def send(self):
        """Send the ON command."""
        super().send()

    # pylint: disable=arguments-differ
    async def async_send(self):
        """Send the ON command async."""
        return await super().async_send(on_level=self._group)