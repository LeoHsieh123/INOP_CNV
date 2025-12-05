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
# Standard Python library imports
from __future__ import absolute_import
import json
import time

# Local package imports
import devices.common.ethspy_commands


class Carlsville(devices.common.ethspy_commands.EthSpyCommands):
    """This class overrides and provides methods to control Carlsville."""

    def __init__(self, port):
        """Initialize a Carlsville object."""
        self.phy_type = 'ORCA'

        super(Carlsville, self).__init__(port)

        self.codename = 'Carlsville'
        self.interface = 'base_t'
        self.highest_speed = '10G'
        self.snr_type = ['EYE-SCORE-HOST']
        self.snr_unit_of_measure = ''
        self.tap = None

        self.lanes = 4

    def ethspy_lane_get_status(self, lane):
        """Lane status is unavailable for Carlsville.

        Args:
            lane (int): Unused, for compatibility only.

        Returns:
            dict: {'OUTPUT': 'N/A'}
        """
        return {'OUTPUT': 'N/A'}

    def ethspy_link_get_status(self):
        """Query the link status and return it.

        Returns:
            dict: The current link status.
        """
        try:
            cmd = 'hostCommand ETHSPY LINK GET-STATUS PHY:{} SIDE:LINE'
            output = json.loads(self.port.execute(cmd.format(self.phy_type)))
        except ValueError:
            output = {}

        return output

    def ethspy_rx_get_snr(self, abort, lane=0, ):
        """Get the SNR-OP-MARGIN from Carlsville and return it.

        Args:
            abort (int): Unused, for compatibility only.
            lane (int): The lane to get the SNR margin from.

        Returns:
            dict: The SNR-OP-MARGIN of the specified lane.
        """
        try:
            r = json.loads(
                self.port.execute(
                    'hostCommand ETHSPY RX GET-STATUS PHY:{} SIDE:LINE L:{}'.format(
                        self.phy_type, lane
                    )
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

    def ethspy_rx_get_status(self, lane):
        """Query the Rx status and return the results.

        Args:
            lane (int): The lane to run the command on.

        Returns:
            dict: The current Rx status.
        """
        try:
            output = json.loads(
                self.port.execute(
                    'hostCommand ETHSPY RX GET-STATUS PHY:{} SIDE:LINE L:{}'.format(
                        self.phy_type, lane
                    )
                )
            )
        except ValueError:
            output = {}

        return output

    def ethspy_tx_get_status(self, lane):
        """The Tx status is unavailable for Carlsville.

        Args:
            lane (int): Unused, for compatibility only.

        Returns:
            dict: {'OUTPUT': 'N/A'}
        """
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
            self.speed = str(int(output['SPEED']) // 1000) + 'G'
            if self.speed == '0G':
                self.speed = '100M'
            if self.speed == '2G':
                self.speed = '2.5G'
        except KeyError:
            self.speed = 'ERROR'

        return self.speed

    def set_base_t_auto_neg(self, speeds=('100M', '1G', '2.5G', '5G', '10G')):
        speed_list = ['100M', '1G', '2.5G', '5G', '10G']

        for new_spd in speeds:
            self.port.execute(f'hostCommand ETHSPY LINK SET-CAPABILITY PHY:ORCA SIDE:LINE SPD:{new_spd[0:-5]}')

    def enable_link_management(self):
        self.port.execute(f'hostCommand ETHSPY LINK ENABLE-LINK-MANAGEMENT PHY:TAMAR_FVL EN:TRUE')

    def disable_link_management(self):
        self.port.execute(f'hostCommand ETHSPY LINK ENABLE-LINK-MANAGEMENT PHY:TAMAR_FVL EN:FALSE')
    
    def force_base_t_speed(self, speed):
        command = f'hostCommand ETHSPY LINK SET-CAPABILITY PHY:ORCA SIDE:LINE SPD:{speed[0:-5]}'
		# print(f'EthSpy command: {command}'
        self.port.execute(command)

    def ethspy_link_get_ttl(self):
        """Get the time-to-link (TTL) and return the results.

        Returns:
            dict: The TTL results
        """
        try:
            output = json.loads(
                self.port.execute(
                    'hostCommand ETHSPY LINK GET-TTL PHY:{} SIDE:LINE T:60000 PS:100'.format(
                        self.phy_type
                    )
                )
            )
        except ValueError:
            print('Warning: Could not parse TTL output!')
            output = {}

        return output
