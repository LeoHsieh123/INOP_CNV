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
import ethspylib
import json
import string
import time


class Lewisberg(devices.common.ethspy_commands.EthSpyCommands):
    """This class overrides and provides methods specific to Lewisberg."""

    def __init__(self, port):
        """Constructor for Lewisberg"""
        self.phy_type = 'KEREM73'

        super(Lewisberg, self).__init__(port)

        self.codename = 'Lewisberg'
        self.interface = 'hss'
        self.snr_type = ['EHM12_NEG', 'EHM12_POS']
        self.snr_unit_of_measure = ' (mV)'
        self.tap = 1

    @staticmethod
    def ethspy_rx_get_snr(abort, lane):
        """No longer valid... returns {'SNR': 'WinPython not available'}"""
        return {'SNR': 'WinPython not available'}

    def ethspy_rx_get_ehm(self, abort, lane):
        """Get the EHM from Lewisberg and return it.

        :param int lane: The lane to retrieve the EHM from
        :return: The EHM values
        :rtype: float
        """
        print('\nPolling EHM12. This will take '
               'about 40 seconds. Please wait...')

        output = {}
        result = self.port.execute(
            'hostCommand ETHSPY RX GET-EHM PHY:{} SIDE:LINE'.format(
                self.phy_type
            )
        )

        if 'warning' in result.lower():
            if abort - 1 > 0:
                print('\nRetrying EHM measurement...')
                self.ethspy_rx_get_ehm(abort - 1, lane)
            else:
                print(
                    'Warning: Unable to get VBCM data! Please try cold '
                    'booting (fully unplugging) the system!'
                )
                output = None
        else:
            try:
                pos_cf = json.loads(
                    self.port.execute(
                        'hostCommand ETHSPY RX GET-EHM PHY:{} POS-CF'.format(
                            self.phy_type
                        )
                    )
                )
            except ValueError:
                pos_cf = {}

            try:
                neg_cf = json.loads(
                    self.port.execute(
                        'hostCommand ETHSPY RX GET-EHM PHY:{} NEG-CF'.format(
                            self.phy_type
                        )
                    )
                )
            except ValueError:
                neg_cf = {}

            output.update(pos_cf)
            output.update(neg_cf)

        return output

    def ethspy_rx_get_vbcm(self):
        ehm = self.ethspy_rx_get_ehm(3, 0)

        if ehm is not None:
            output = self.port.execute(
                'hostCommand ETHSPY RX GET-EHM PHY:{} SIDE:LINE VBCM-TOOLS'.format(
                    self.phy_type
                )
            )
        else:
            output = None

        return output

    def ethspy_rx_get_ehm_moncal_data(self):
        """Get the MON-CAL data for EHM post-processing.
        
        Returns:
            str: Formatted string of the MON-CAL data.
        """
        output = self.port.execute(
            'hostcommand ETHSPY RX GET-EHM MONCAL-DATA PHY:{} SIDE:LINE'.format(
                self.phy_type
            )
        )

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
        """Query the currently set coefficients and return them.
        
        The lane argument is not used for Lewisburg and defaults to 0. 
        The output dictionary is formatted as LANE keys with a dictionary 
        containing the coefficients as the value.

        Args:
            lane (int): (Unused, for compatibility only. Forced to 0.)

        Returns:
            dict: The currently set coefficients.
        """
        coeffs = json.loads(
            self.port.execute('hostCommand ETHSPY TX GET-STATUS 0')
        )

        # Need to turn the new style into the old style
        output_dict = {
            0: {
                'LANE': 0,
                'MODE': 'SFI10G',
                'CM1': coeffs['TX-COEFFS']['SFI-10G-DA']['CM1'],
                'C0': coeffs['TX-COEFFS']['SFI-10G-DA']['C0'],
                'C1': coeffs['TX-COEFFS']['SFI-10G-DA']['C1'],
                'BLC': coeffs['TX-COEFFS']['SFI-10G-DA']['BAL-LEG-CONTROL'],
                'BLS': coeffs['TX-COEFFS']['SFI-10G-DA']['BAL-LEG-STATUS']
            }
        }

        return output_dict

    def hss(self, mode=-1, pattern=-1, lane=-1, cm1=None, c0=None, c1=None):
        """Control the high-speed serial output of Lewisberg.
        
        All of the arguments are optional. 
        If any are left out, they will not be changed.
        
        Args:
            lane (int): The mode to set the DUT into.
            mode (str): The pattern to output, (SQUARE8, PRBS9, PRBS31).
            pattern (str): The lane to set.
            cm1 (int): The pre-cursor value.
            c0 (int): The cursor value.
            c1 (int): The post-cursor value.

        Returns:
            dict: The newly set coefficients.
        """
        print('\nLBG: Running the HSS command...')

        defaults = self.get_coeffs(lane)

        if cm1 is None:
            cm1 = defaults[lane]['CM1']
        if c0 is None:
            c0 = defaults[lane]['C0']
        if c1 is None:
            c1 = defaults[lane]['C1']

        unformatted_force_string = (
            'hostCommand ETHSPY TX SET-TXFFE-FORCE L:%s CM1:%s '
            'C0:%s C1:%s T:SFI-10G-DA BLS:%s BLC:%s'
        )
        self.port.execute(
            unformatted_force_string % (
                lane, cm1, c0, c1, defaults[lane]['BLS'], defaults[lane]['BLC']
            )
        )

        if pattern in ['PRBS9', 'PRBS31', 'SQUARE8']:
            self.port.execute(
                'hostCommand ETHSPY TX SET-PATTERN %s %s' % (
                    lane, pattern
                )
            )

        coeffs = self.get_coeffs(lane)

        return coeffs
