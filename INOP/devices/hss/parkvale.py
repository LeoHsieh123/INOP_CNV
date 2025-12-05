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
import json

# Local package imports
import ethspylib
from ..common.ethspy_commands import EthSpyCommands


class Parkvale(EthSpyCommands):
    """This class overrides and provides methods for controlling Parkvale devices."""

    def __init__(self, port):
        """Constructor for Parkvale"""
        self.phy_type = 'PKVL'

        super(Parkvale, self).__init__(port)

        self.codename = 'Parkvale'
        self.interface = 'hss'
        self.snr_type = ['EYE-HEIGHT']
        self.snr_unit_of_measure = ' (mV)'
        self.tap = -1

        # self.set_mode()

    def ethspy_lane_get_status(self, lane):
        """This method returns {'OUTPUT': 'N/A'} for compatibility.

        Args:
            lane (int): (Unused, for compatibility only.)

        Returns:
            dict: {'OUTPUT': 'N/A'}
        """
        return {'OUTPUT': 'N/A'}

    def ethspy_link_get_stats(self):
        """Gets the link stats and adds the QR counters to the output.

        Returns:
            dict: The link stats with QR counters added.
        """
        try:
            stats_output = json.loads(self.port.execute('hostCommand ETHSPY LINK GET-STATS'))
            good_rx, rx_errors = self.get_qr_counter()
            stats_output['QR-GOOD-RECEIVES'] = good_rx
            stats_output['QR-RECEIVE-ERRORS'] = rx_errors
        except ValueError:
            print('Could not get or convert output from ETHSPY LINK GET-STATS command!')
            stats_output = {}

        return stats_output

    def ethspy_link_get_status(self):
        """This method reads the output of ETHSPY LINK GET-STATUS and adds a LINK-UP key based on the PHY-LINK-UP key.

        Returns:
            dict: Modified output of ETHSPY LINK GET-STATUS
        """
        output = super(Parkvale, self).ethspy_link_get_status()

        if 'PHY-LINK-UP' in output:
            if output['PHY-LINK-UP']:
                output['LINK-UP'] = True
            else:
                output['LINK-UP'] = False

        return output

    def ethspy_packet_enable_generator(self):
        self.port.execute('hostCommand ETHSPY PACKET ENABLE-GENERATOR 0')

    def ethspy_packet_enable_checker(self):
        self.port.execute('hostCommand ETHSPY PACKET ENABLE-CHECKER 0 TRUE')

    def ethspy_rx_get_snr(self, abort, lane, e_phy=True):
        """Get the VOM from Parkvale and return it.

        Args:
            abort (int): (Unused, for compatibility only.)
            lane (int): The lane to retrieve the VOM from.
            e_phy (bool): If True, get the VOM from the external phy.

        Returns:
            dict: The VOM from the specified lane.
        """
        try:
            output = json.loads(
                self.port.execute(
                    'hostCommand ETHSPY RX GET-VOM PHY:{} SIDE:LINE {}'.format(
                        self.phy_type, lane
                    )
                )
            )
        except ValueError:
            output = {}

        return output

    def ethspy_tx_get_status(self, lane):
        """Query the Tx status and return the results.

        Args:
            lane (int): The lane to run the command on.

        Returns:
            dict: The current Tx status.
        """
        try:
            output = json.loads(
                self.port.execute(f'hostCommand ETHSPY TX GET-STATUS PHY:PKVL SIDE:LINE L:{lane}')
            )
        except ValueError:
            output = {}

        return output
    
    def get_initial_coeffs(self, lane=-1):
        """Gets the initial coeffs from the Parkvale device.

        Args:
            lane (int): The lane to get the coefficients from.

        Returns:
            dict: The current coefficients.
        """
        title = 'User Intervention Required'

        cable_text = 'Please insert a cable with an appropriate link partner (10G or 25G).'
        hcb_text = 'Please insert the HCB.'

        ethspylib.message_box(ethspylib.MESSAGE_BOX_INFO, title, cable_text)

        initial_coeffs = self.get_coeffs(lane)
        
        initial_coeffs[lane]['CM1'] = initial_coeffs[lane]['FORCED-CM1']
        initial_coeffs[lane]['C0'] = initial_coeffs[lane]['FORCED-C0']
        initial_coeffs[lane]['C1'] = initial_coeffs[lane]['FORCED-C1']
        print(f'Initial Coeffs: {initial_coeffs}')

        ethspylib.message_box(ethspylib.MESSAGE_BOX_INFO, title, hcb_text)

        return initial_coeffs

    def get_coeffs(self, lane=-1):
        """Query the current coefficients and return them.

        If a lane is not specified, coefficients for all lanes will be
        returned. The return dictionary is organized by lane.

        Args:
            lane (int): The lane to get the coefficients from

        Returns:
            dict: The currently set coefficients.
        """
        command = 'hostCommand ETHSPY TX GET-STATUS PHY:{} SIDE:LINE L:{}'
        output_dict = {}

        if lane == -1:
            for dut_lane in range(0, 4):
                try:
                    coeffs = json.loads(
                        self.port.execute(command.format(self.phy_type, dut_lane))
                    )
                except ValueError:
                    coeffs = None
    
                if coeffs:
                    output_dict[dut_lane] = coeffs
                    output_dict[dut_lane]['LANE'] = dut_lane
        else:
            try:
                coeffs = json.loads(
                    self.port.execute(command.format(self.phy_type, lane))
                )
            except ValueError:
                coeffs = None

            if coeffs:
                output_dict[lane] = coeffs
                output_dict[lane]['LANE'] = lane

        return output_dict
    
    def hss(self, mode=None, pattern=None, lane=0, cm1=None, c0=None, c1=None):
        """Control the high-speed serial output of Parkvale.

        All of the arguments are required.

        1. 'ETHSPY LINK ENABLE-LINK-MANAGEMENT EN:FALSE'
        2. 'ETHSPY TX SET-PATTERN L: SPD:25G PAT: TX: PRE: GE:'
        3. 'ETHSPY TX SET-TXFFE-FORCE L: CM1: C0: C1:'

        Args:
            mode (str): The mode to set the DUT into.
            pattern (str): The pattern to output, PRBS/7/9/11/23/31/SQUARE/1/2/4/8/ONES/ZEROS
            lane (int): The lane to set.
            cm1 (int): The pre1-cursor value.
            c0 (int): The cursor value.
            c1 (int): The post-cursor value.

        Returns:
            dict: The newly set coefficients.
        """
        print('\nDUT: Running the HSS command...')

        mode_map = {
            '25GBASE_SR': '25G',
            'SFI10G': '10G'
        }

        self.port.execute(
            'hostCommand ETHSPY LINK ENABLE-LINK-MANAGEMENT EN:FALSE'
        )

        if cm1 is not None and c0 is not None and c1 is not None:
            self.port.execute(
                'hostCommand ETHSPY TX SET-TXFFE-FORCE PHY:PKVL SIDE:LINE L:0 CM1:{} C0:{} C1:{}'.format(
                    cm1, c0, c1
                )
            )

        if mode is not None and pattern is not None:
            self.port.execute(
                'hostCommand ETHSPY TX SET-PATTERN PHY:PKVL SIDE:LINE L:0 SPD:{} PAT:{}'.format(
                    mode_map[mode], pattern
                )
            )

        coeffs = self.get_coeffs(lane)

        return coeffs
    def set_mode(self):
        self.port.execute(
            'hostCommand ETHSPY LINK SET-PMD P100CR-P100CR'
        )

    def status(self, *args, **kwargs):
        output = self.ethspy_link_get_status()

        if output['LINK-UP'] == True:
            output['LINK'] = 'UP'
        else:
            output['LINK'] = 'DOWN'

        output['SPEED'] = output['CURRENT-LINK-SPEED']

        return output

    @staticmethod
    def ethspy_module_info_get_all():
        return {'VENDOR NAME': 'Unspecified', 'VENDOR PN': 'Unspecified'}

