from __future__ import absolute_import
import devices.common.legacy_to_ethspy_converter as converter


class Twinville(converter.LegacyToEthspyConverter):
    """The class sets variables specific to Twinville."""

    def __init__(self, port):
        super(Twinville, self).__init__(port)

        self.codename = 'Twinville'
        self.interface = 'base_t'
        self.highest_speed = '10G'

    def ethspy_link_get_ttl(self):
        output = super(Twinville, self).ethspy_link_get_ttl()

        # Workaraound for Twinville
        self.reset()

        return output
