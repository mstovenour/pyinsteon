from binascii import unhexlify
from tests import _LOGGER, set_log_levels
import unittest
import sys

from pyinsteon.constants import MessageId
from pyinsteon.protocol.messages.outbound import get_next_all_link_record
from tests.test_messages.test_outbound.outbound_base import OutboundBase


class TestGetNextAllLinkRecord(unittest.TestCase, OutboundBase):
    def setUp(self):
        self.hex = "026A"
        super(TestGetNextAllLinkRecord, self).base_setup(
            MessageId.GET_NEXT_ALL_LINK_RECORD, unhexlify(self.hex)
        )
        set_log_levels(
            logger="debug",
            logger_pyinsteon="info",
            logger_messages="info",
            logger_topics=False,
        )


if __name__ == "__main__":
    unittest.main()