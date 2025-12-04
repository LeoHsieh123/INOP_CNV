##############################################################################
# INTEL CONFIDENTIAL
# Copyright 2020 Intel Corporation All Rights Reserved.
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
"""This module is used to control Connorsville Intel(R) Ethernet devices.

    Typical usage example:
        cnv = Connorsville(9)
        link_status = cnv.ethspy_link_get_status()
"""
# Standard library imports
import json

# Local application imports
# import devices.common.ethspy_commands
import ethspylib
from ..common.ethspy_commands import EthSpyCommands
# import devices.common.ethspy_commands


class Connorsville(EthSpyCommands):
    """This class overrides and provides methods specific to Connorsville."""

    def __init__(self, port):
        self.phy_type = 'CNV'

        super(Connorsville, self).__init__(port)

        self.codename = 'Connorsville'
        self.interface = 'hss'

        if self.ethspy_link_get_status()['FEC-MODE'] == 'RS-544':
            self.snr_type = [
                'EYE-HEIGHT-THLE', 'EYE-HEIGHT-THME', 'EYE-HEIGHT-THUE',
                'EYE-HEIGHT-THLO', 'EYE-HEIGHT-THMO', 'EYE-HEIGHT-THUO'
            ]
        else:
            self.snr_type = ['EYE-HEIGHT-THLE', 'EYE-HEIGHT-THLO']

        self.snr_unit_of_measure = ' (mV)'


    def ethspy_lane_get_status(self, lane):
        """This method returns {'OUTPUT': 'N/A'} for compatibility.

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

    @staticmethod
    def ethspy_rx_get_training_coeff_logs(lane=0):
        """This method returns {'OUTPUT': 'N/A'} for compatibility.

        Args:
            lane (int): Unused. For compatibility only.

        Returns:
            dict: {'OUTPUT': 'N/A'}
        """
        return {}

    def ethspy_tx_get_status(self, lane):
        """This method returns {'OUTPUT': 'N/A'} for compatibility.

        Returns:
            dict: {'OUTPUT': 'N/A'}
        """
        return {'OUTPUT': 'N/A'}

    def ethspy_rx_get_snr(self, abort, lane=0):
        """Get the EHM from CVL and return it.
           This method is pending developed understanding of API call in CVL

        Args:
            abort (int): Unused. For compatibility only.
            lane (int): The lane to get the EHM from.

        Returns:
            dict: The EHM of the specified lane.
        """
        #print('Getting the EHM. This may take a few seconds...')
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

    def get_initial_coeffs(self, lane=-1):
        """Gets the initial coeffs from the Columbiaville device.

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

    def hss(self, mode=None, pattern=None, lane=0, c_minus_one=None, c_zero=None, c_one=None):
        # pylint: disable=(too-many-arguments)
        """Control the high-speed serial output of Columbiaville.

        All of the arguments are required.

        1. 'ETHSPY LINK ENABLE-LINK-MANAGEMENT EN:FALSE'
        2. 'ETHSPY TX SET-PATTERN L: SPD:25G PAT: TX: PRE: GE:'
        3. 'ETHSPY TX SET-TXFFE-FORCE L: CM3: CM2: CM1: C0: C1:'

        Args:
            mode (str): The mode to set the DUT into.
            pattern (str): The output pattern, SQUARE8, SQUARE1, PRBS9, PRBS31.
            lane (int): The lane to set.
            c_minus_one (int): The pre1-cursor value.
            c_zero (int): The cursor value.
            c_one (int): The post-cursor value.

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

        if mode is not None and pattern is not None:
            set_pattern_cmd = 'ETHSPY TX SET-PATTERN'
            self.port.execute(
                'hostCommand {} PHY:CVL L:ALL SPD:{} PAT:{} TX:FALSE PRE:FALSE GE:FALSE'.format(
                    set_pattern_cmd, mode_map[mode], pattern
                )
            )

        if c_minus_one is not None and c_zero is not None and c_one is not None:
            txffe_cmd = 'ETHSPY TX SET-TXFFE-FORCE'
            self.port.execute(
                'hostCommand {} PHY:CVL L:ALL CM3:0 CM2:0 CM1:{} C0:{} C1:{}'.format(
                    txffe_cmd, c_minus_one, c_zero, c_one
                )
            )

        coeffs = self.get_coeffs(lane)

        return coeffs

    def ethspy_module_info_get_all(self):
        """Reads the connector module info.

        Returns:
            dict: Connector module info.
        """
        data = json.loads(self.port.execute('hostCommand ETHSPY LINK GET-MODULE-INFO'))
        keys = list(data.keys())

        for key in keys:
            data[key.upper()] = data.pop(key)

        return data
