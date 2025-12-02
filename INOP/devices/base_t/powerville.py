from __future__ import absolute_import
import devices.common.legacy_to_ethspy_converter as converter


class Powerville(converter.LegacyToEthspyConverter):
    """The class sets variables specific to Powerville."""

    def __init__(self, port):
        super(Powerville, self).__init__(port)

        self.codename = 'Powerville'
        self.interface = 'base_t'
        self.highest_speed = '1G'
