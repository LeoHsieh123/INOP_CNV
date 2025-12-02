##############################################################################
# INTEL CONFIDENTIAL
# Copyright 2016 2017 Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related
# to the source code (Material) are owned by Intel Corporation or its
# suppliers or licensors. Title to the Material remains with Intel Corp-
# oration or its suppliers and licensors. The Material may contain trade
# secrets and proprietary and confidential information of Intel Corpor-
# ation and its suppliers and licensors, and is protected by worldwide
# copyright and trade secret laws and treaty provisions. No part of the
# Material may be used, copied, reproduced, modified, published, uploaded,
# posted, transmitted, distributed, or disclosed in any way without
# Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellect-
# ual property right is granted to or conferred upon you by disclosure or
# delivery of the Materials, either expressly, by implication, inducement,
# estoppel or otherwise. Any license under such intellectual property
# rights must be express and approved by Intel in writing.
##############################################################################
from __future__ import absolute_import
import devices.common.ethspy_commands
import json


class Coppervale(devices.common.ethspy_commands.EthSpyCommands):
    """This class provides methods specific to Coppervale."""

    def __init__(self, port):
        self.phy_type = 'CPVL'

        super(Coppervale, self).__init__(port)

        self.codename = 'Coppervale'
        self.interface = 'base_t'
        self.highest_speed = '10G'
        self.snr_type = ['EYE-SCORE-HOST']
        self.snr_unit_of_measure = ''
        self.tap = None
        self.speed = '10G'
        self.lanes = 4

        self.nvm_version = self.get_nvm_version()
        self.firmware_revision = self.get_firmware_revision()

    def ethspy_lane_get_status(self, lane):
        return {'OUTPUT': 'N/A'}

    def ethspy_module_info_get_all(self):
        """Return blank information for Coppervale."""
        return {'VENDOR NAME': 'N/A', 'VENDOR PN': 'N/A', 'VENDOR OUI': 'N/A'}

    def ethspy_rx_get_snr(self, abort, lane=0, ):
        try:
            r = json.loads(
                self.port.execute(
                    'hostCommand ETHSPY RX GET-STATUS PHY:CPVL SIDE:LINE %s' % lane
                )
            )
        except ValueError:
            r = {}

        output = {}
        try:
            output['SNR-OP-MARGIN'] = r['SNR-OP-MARGIN']
        except KeyError:
            output['SNR-OP-MARGIN'] = 'N/A'

        try:
            output['SNR-MIN-OP-MARGIN'] = r['SNR-MIN-OP-MARGIN']
        except KeyError:
            output['SNR-MIN-OP-MARGIN'] = 'N/A'

        return output

    def ethspy_tx_get_status(self, lane):
        return {'OUTPUT': 'N/A'}

    def get_speed(self):
        """Extract the device speed from the "STATUS" command and return it.

        You can pass in the output from :meth:`DUT.status` and it will extract the speed from the
        output. If you do not pass anything in, it will run the STATUS command for you and return
        the speed.

        :param str ea_input: The output from the :meth:`DUT.status` method
        :return: The device speed
        :rtype: int
        :raises EthSpyError: if it could not extract the device speed
        """
        output = self.dictify(self.port.execute('hostCommand STATUS'))
        try:
            if output['SPEED'] == 'NA':
                self.speed = 'NA'
                return self.speed
            self.speed = str(int(output['SPEED'])//1000) + 'G'
            if self.speed == '0G':
                self.speed = '100M'
            if self.speed == '2G':
                self.speed = '2.5G'
        except KeyError:
            self.speed = 'ERROR'

        return self.speed
