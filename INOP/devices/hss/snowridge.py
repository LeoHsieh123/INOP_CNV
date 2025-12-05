"""
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
"""
import json
import string
import time
import devices.common.ethspy_commands


class Snowridge(devices.common.ethspy_commands.EthSpyCommands):
    """This class overrides and provides methods specific to Snowridge."""

    def __init__(self, port):
        """Constructor for Snowridge"""
        self.phy_type = 'RIMMON'

        super(Snowridge, self).__init__(port)

        self.codename = 'Snowridge'
        self.interface = 'hss'
        self.snr_type = ''
        self.snr_unit_of_measure = ''
        self.tap = 1
        self.tap_settings = [[0, 41, 0, 'tap0']]
        self.caui_coeffs = [[0, 41, 0]]

    def ethspy_rx_get_snr(self, abort, lane=0, ):
        """Get the EHM from Rimmon and return it.
           This method is pending developed understanding of API call in Rimmon

        Args:
            abort (int): Unused, for compatibility only.
            lane (int): The lane to get the EHM from.

        Returns:
            dict: The EHM of the specified lane.
        """
        print('Getting the EHM. This may take a few seconds...')
        try:
            output = json.loads(
                self.port.execute(
                    'hostCommand ETHSPY RX GET-EHM PHY:{} SIDE:LINE L:{}'.format(
                        self.phy_type, lane
                    )
                )
            )
        except ValueError:
            output = {}

        return output

    def ethspy_lane_get_status(self, lane):
        """This method returns {'OUTPUT': 'N/A'} for compatibility.

        Args:
            lane (int): (Unused, for compatibility only.)

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

    def ethspy_rx_get_training_coeff_logs(self, lane):
        """This method returns {'OUTPUT': 'N/A'} for compatibility.

        Args:
            lane (int): (Unused, for compatibility only.)

        Returns:
            dict: {'OUTPUT': 'N/A'}
        """
        return {}

    def ethspy_tx_get_status(self, lane):
        """This method returns {'OUTPUT': 'N/A'} for compatibility.

        Args:
            lane (int): (Unused, for compatibility only.)

        Returns:
            dict: {'OUTPUT': 'N/A'}
        """
        return {'OUTPUT': 'N/A'}

    def ethspy_rx_get_ehm(self, abort, lane=0, ):
        """Get the EHM from SNR-NS and return it.

        Args:
            abort (int): Unused, for compatibility only.
            lane (int): The lane to get the EHM from.

        Returns:
            dict: The EHM of the specified lane.
        """
        print('Getting the EHM. This may take a few seconds...')
        try:
            output = json.loads(
                self.port.execute(
                    'hostCommand ETHSPY RX GET-EHM PHY:{} SIDE:LINE L:{}'.format(
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

    def get_coeffs(self, lane=-1, e_phy=False):
        """Query the current coefficients and return them.

        If a lane is not specified, coefficients for all lanes will be
        returned. The return dictionary is organized by lane.

        Args:
            lane (int): The lane to get the coefficients from
            e_phy (bool): (Unused, for compatibility only)

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
        """Control the high-speed serial output of Rimmon.

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
            '25GBASE_SR': '25GS',
            'SFI10G': '10GS'
        }

        self.port.execute(
            'hostCommand ETHSPY LINK ENABLE-LINK-MANAGEMENT EN:FALSE'
        )

        if mode is not None and pattern is not None:
            self.port.execute(
                'hostCommand ETHSPY TX SET-PATTERN PHY:RIMMON SIDE:LINE L:0 SPD:{} PAT:{} TX:TRUE'.format(
                    mode_map[mode], pattern
                )
            )

        if cm1 is not None and c0 is not None and c1 is not None:
            self.port.execute(
                'hostCommand ETHSPY TX SET-TXFFE-FORCE PHY:RIMMON SIDE:LINE L:0 CM1:{} C0:{} C1:{}'.format(
                    cm1, c0, c1
                )
            )

        coeffs = self.get_coeffs(lane)

        return coeffs

    def ethspy_module_info_get_all(self):
        """Attempt to get the module info.

        Args:
            None

        Returns:
            dict: The module info or an empty dictionary if it cannot be obtained.
        """
        raw_data = self.port.execute(f'hostCommand ETHSPY LINK GET-MODULE-INFO PHY:{self.phy_type}')

        # time.sleep(10)

        # filter now returns an iterator so we need to break it down
        data = ''.join([i for i in filter(string.printable.__contains__, raw_data)])

        try:
            j_data = json.loads(data)

            if 'VENDOR NAME' not in j_data:
                j_data['VENDOR NAME'] = 'Unspecified'

            if 'VENDOR PN' not in j_data:
                j_data['VENDOR PN'] = 'Unspecified'

            j_data.pop('VALID-COMMANDS', None)

        except ValueError:
            j_data = {}

        for key in j_data:
            try:
                # Remove multiple whitespace characters
                j_data[key] = ' '.join(j_data[key].split())

                # Strip out characters that cause problems for filenames
                safe = '._-()+[]'

                j_data[key] = ''.join(
                    [x if x.isalnum() or x in safe else '_' for x in j_data[key]]
                )

            except (AttributeError, TypeError):
                pass

        if not j_data:
            j_data = {'VENDOR NAME': 'Unspecified', 'VENDOR PN': 'Unspecified'}

        return j_data
