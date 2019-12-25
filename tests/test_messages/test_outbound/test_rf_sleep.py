from binascii import unhexlify
from tests import _LOGGER, set_log_levels
import unittest
import sys

from pyinsteon.constants import MessageId
from pyinsteon.protocol.messages.outbound import rf_sleep
from tests.test_messages.test_outbound.outbound_base import OutboundBase


class TestRfSleep(unittest.TestCase, OutboundBase):
    def setUp(self):
        self.hex = "0272"
        super(TestRfSleep, self).base_setup(MessageId.RF_SLEEP, unhexlify(self.hex))
        set_log_levels(
            logger="debug",
            logger_pyinsteon="info",
            logger_messages="info",
            logger_topics=False,
        )


if __name__ == "__main__":
    unittest.main()