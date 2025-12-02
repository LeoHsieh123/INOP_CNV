from __future__ import absolute_import
import devices.common.legacy_to_ethspy_converter as converter


class Springville(converter.LegacyToEthspyConverter):
    """The class sets variables specific to Springville."""

    def __init__(self, port):
        super(Springville, self).__init__(port)

        self.codename = 'Springville'
        self.interface = 'base_t'
        self.highest_speed = '1G'
