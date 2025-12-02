from __future__ import absolute_import
import devices.common.legacy_to_ethspy_converter as converter


class BartonHills(converter.LegacyToEthspyConverter):
    """The class sets variables specific to BartonHills."""

    def __init__(self, port):
        super(BartonHills, self).__init__(port)

        self.codename = 'BartonHills'
        self.interface = 'base_t'
        self.highest_speed = '1G'
