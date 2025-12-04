from __future__ import absolute_import
import devices.common.legacy_to_ethspy_converter as converter


class Hartwell(converter.LegacyToEthspyConverter):
    """The class sets variables specific to Hartwell."""

    def __init__(self, port):
        super(Hartwell, self).__init__(port)

        self.codename = 'Hartwell'
        self.interface = 'base_t'
        self.highest_speed = '1G'
