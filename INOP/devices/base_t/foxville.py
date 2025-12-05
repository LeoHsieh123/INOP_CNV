"""This module provides a class to control Foxville devices.

    Typical usage example:
        fxvl = Foxville(11)
        link_status = fxvl.ethspy_link_get_status()

INTEL CONFIDENTIAL
Copyright 2016 2017 Intel Corporation All Rights Reserved.

The source code contained or described herein and all documents related
to the source code (Material) are owned by Intel Corporation or its
suppliers or licensors. Title to the Material remains with Intel Corp-
oration or its suppliers and licensors. The Material may contain trade
secrets and proprietary and confidential information of Intel Corpor-
ation and its suppliers and licensors, and is protected by worldwide
copyright and trade secret laws and treaty provisions. No part of the
Material may be used, copied, reproduced, modified, published, uploaded,
posted, transmitted, distributed, or disclosed in any way without
Intel's prior express written permission.

No license under any patent, copyright, trade secret or other intellect-
ual property right is granted to or conferred upon you by disclosure or
delivery of the Materials, either expressly, by implication, inducement,
estoppel or otherwise. Any license under such intellectual property
rights must be express and approved by Intel in writing.
"""

# Standard library imports
import json

# Local application imports
from devices.common.legacy_to_ethspy_converter import LegacyToEthspyConverter


class Foxville(LegacyToEthspyConverter):
    """This class overrides and provides methods to control Foxville."""

    def __init__(self, port):
        """Initialize a new Foxville object.

        Args:
            port (int): The EthAgent port that the Foxville device is connected to.

        Returns:
            None
        """
        self.phy_type = 'P31G'

        super(Foxville, self).__init__(port)

        self.codename = 'Foxville'
        self.interface = 'base_t'
        self.highest_speed = '10G'
        self.snr_type = ['EYE-SCORE-HOST']
        self.snr_unit_of_measure = ''
        self.tap = None

        self.lanes = 4

    def get_speed(self):
        """Extracts the device speed from the "STATUS" command and returns it.

        You can pass in the output from :meth:`DUT.status` and it will extract the speed from the
        output. If you do not pass anything in, it will run the STATUS command for you and return
        the speed.

        Returns:
            str: The device speed
        """
        output = self.dictify(self.port.execute('hostCommand STATUS'))
        try:
            if output['SPEED'] == 'NA':
                self.speed = 'NA'
                return self.speed
            self.speed = str(int(output['SPEED']) // 1000) + 'G'
            if self.speed == '0G':
                self.speed = '100M'
            if self.speed == '2G':
                self.speed = '2.5G'
        except KeyError:
            self.speed = 'ERROR'

        return self.speed

