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
from __future__ import print_function
from __future__ import absolute_import
from . import legacy_commands


class LegacyToEthspyConverter(legacy_commands.LegacyCommands):
    """This class "converts" the legacy commands into Ethspy commands."""

    def __init__(self, port):
        """Constructor for LegacyToEthspyConverter"""
        super(LegacyToEthspyConverter, self).__init__(port)

        self.phy_type = None
        self.snr_type = ['SNR']
        self.tap = None
        self.lanes = 4

    def ethspy_link_get_stats(self):
        """Get the Tx/Rx stats and return them.

        The output of the QR and QT counters are added to the output.

        This method does NOT use the ETHSPY LINK GET-STATS command as it
            doesn't exist in the legacy command set. It uses the legacy
            GETSTATS command and converts the output to a dictionary.

        Returns:
            dict: The Tx/Rx stats.
        """
        try:
            stats_output = self.getstats()
            good_rx, rx_errors = self.get_qr_counter()
            good_tx, tx_errors = self.get_qt_counter()
            stats_output['QR-GOOD-RECEIVES'] = good_rx
            stats_output['QR-RECEIVE-ERRORS'] = rx_errors
            stats_output['QT-GOOD-TRANSMITS'] = good_tx
            stats_output['QT-TRANSMIT-ERRORS'] = tx_errors
        except ValueError:
            print('Could not get or convert output from the GETSTATS command!')
            stats_output = {}

        return stats_output

    def ethspy_link_get_ttl(self):
        """Run the time-to-link (TTL) command and return the results.

        This does NOT use the ETHSPY command since it does not exist for
            for legacy devices. It uses the the TTL command instead.

        Returns:
            dict: The TTL results.
        """
        ttl = self.ttl()

        if 'ERROR' not in ttl:
            output = ttl
            output.update({'ERROR': 'None'})
        else:
            print('Warning: TTL did not run correctly!')
            output = {'Link TTL(ms)': 'ERROR'}

        return output

    def ethspy_link_get_status(self):
        """Query the link status and return the results.

        This method does NOT use the ETHSPY command since it does not 
            exist for legacy devices. It uses the STATUS command instead.

        Returns:
            dict: The current link status.
        """
        output = self.status()

        output['LINK-UP'] = output.pop('LINK', None)
        output['SPEED'] = self.get_speed()

        return output

    def ethspy_module_info_get_all(self):
        return {'VENDOR NAME': 'Unspecified', 'VENDOR PN': 'Unspecified'}

    def ethspy_summary_get_status(self):
        """Get the status summary of the device and return the results.
        
        This method does NOT use the ETHSPY commmand since it does not 
            exist for legacy devices. It uses the INFOLIST command instead.
        
        Returns:
            dict: The summary status of the device.
        """
        return self.infolist()

    @staticmethod
    def ethspy_lane_get_status(lane):
        return {'OUTPUT': 'N/A'}

    @staticmethod
    def ethspy_rx_get_snr(abort, lane):
        return {'SNR': 'N/A'}

    @staticmethod
    def ethspy_rx_get_status(lane):
        return {'OUTPUT': 'N/A'}

    @staticmethod
    def ethspy_tx_get_status(lane):
        return {'OUTPUT': 'N/A'}
