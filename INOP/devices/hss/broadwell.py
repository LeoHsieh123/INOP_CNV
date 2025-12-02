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
import devices.common.ethspy_commands
import json


class Broadwell(devices.common.ethspy_commands.EthSpyCommands):
    """This class provides methods specific to Broadwell."""

    def __init__(self, port):
        """Constructor for the Broadwell device type."""
        self.phy_type = 'KEREM'

        super(Broadwell, self).__init__(port)

        self.codename = 'Broadwell'
        self.interface = 'hss'
        self.snr_type = ['EHM12_NEG', 'EHM12_POS']
        self.snr_unit_of_measure = ' (mV)'
        self.tap = 1

    def ethspy_rx_get_snr(self, abort, lane):
        """Get the EHM from Broadwell and return it.

        :param int lane: The lane to retrieve the EHM from
        :return: The EHM values
        :rtype: float
        """
        print('Polling EHM12. This will take about 15 seconds. Please wait...')

        output = {}
        self.port.execute('hostCommand ETHSPY RX GET-EHM')
        try:
            output.update(
                json.loads(
                    self.port.execute('hostCommand ETHSPY RX GET-EHM POS-CF')
                )
            )
        except ValueError:
            output.update({'10^-12 BER at Positive(mv)': 'ERROR'})

        try:
            output.update(
                json.loads(
                    self.port.execute('hostCommand ETHSPY RX GET-EHM NEG-CF')
                )
            )
        except ValueError:
            output.update({'10^-12 BER at Negative(mv)': 'ERROR'})

        return output

    def ethspy_rx_get_training_coeff_logs(self, lane=0):
        """Run the ETHSPY RX GET-TRAINING-COEFF-LOGS and return the output.

        Args:
            lane (int): The lane to get the training coeff log from.

        Returns:
            str: Training coeff logs
        """
        try:
            output = self.port.execute(
                'hostCommand ETHSPY RX GET-TRAINING-COEFF-LOGS {}'.format(lane)
            )
        except ValueError:
            output = {}

        return output

    def get_coeffs(self, lane=0):
        """Read the currently set coefficients and return them.

        BDX-DE only has one lane so it is defaulted to zero, it doesn't matter what is passed in.
        The return dictionary is organized by lane.

        :param int lane: Unnecessary - for compatibility only
        :return: Currently set coefficients
        :rtype: dict
        """
        coeffs = json.loads(
            self.port.execute('hostCommand ETHSPY TX GET-STATUS 0')
        )

        # Need to turn the new style into the old style
        output_dict = {
            0: {
                'LANE': 0,
                'MODE': 'SFI10G',
                'CM1': coeffs['TX-COEFFS']['OBSERVED']['CM1'],
                'C0': coeffs['TX-COEFFS']['OBSERVED']['C0'],
                'C1': coeffs['TX-COEFFS']['OBSERVED']['C1']
            }
        }

        return output_dict

    def hss(self, mode=None, pattern=None, lane=None, cm1=None, c0=None, c1=None):
        """Control the high-speed serial output.

        All of the arguments except lane are optional.
        If an argument is omitted, it will stay as the currently set value.

        :param int lane: The lane to be controlled
        :param str mode: The mode to set the slot too, e.g. SFI10G, XLPPI, 40GBASE-CR4...
        :param str pattern: The pattern to output, e.g. PRBS9, PRBS31, SQUARE8, SQUARE1...
        :param int cm1: The pre-cursor value
        :param int c0: The main-cursor value
        :param int c1: The post-cursor value
        :return: The updated settings from EthAgent
        :rtype: dict

        .. note::
           For a complete list of values that can be used in the mode and pattern options, check
           the EthAgent documentation (link needs to be added here).
        """
        print('\nSetting the DUT...')

        speed_dict = {'SFI10G': '10GS', 'XLPPI': '40GP', 'CR4': '40GP'}

        if lane:
            current_coeffs = self.get_coeffs(lane)
        else:
            current_coeffs = self.get_coeffs()

        if mode == 'SFI10G':
            self.port.execute(
                'hostCommand ETHSPY LINK SET-CURRENT-SPEED {}'.format(
                    speed_dict[mode]
                )
            )

        if cm1 or c0 or c1:
            if cm1 is not None:
                print('cm1 = ', cm1)
                cm1_str = 'CM1:{}'.format(cm1)
            else:
                cm1_str = 'CM1:{}'.format(current_coeffs['CM1'])

            if c0 is not None:
                print('c0 = ', c0)
                c0_str = 'C0:{}'.format(c0)
            else:
                c0_str = 'C0:{}'.format(current_coeffs['C0'])

            if c1 is not None:
                print("c1 = ", c1)
                c1_str = 'C1:{}'.format(c1)
            else:
                c1_str = 'C1:{}'.format(current_coeffs['C1'])

            self.port.execute(
                'hostCommand ETHSPY TX SET-TXFFE-FORCE L:{} {} {} {} T:KR-INIT'.format(
                    lane, cm1_str, c0_str, c1_str
                )
            )

        if pattern in ['PRBS9', 'PRBS31', 'SQUARE8']:
            print('pattern = ', pattern)
            cmd = 'hostCommand ETHSPY TX SET-PATTERN {} {}'
            self.port.execute(cmd.format(lane, pattern))

        output = self.get_coeffs()

        return output
