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
import devices.common.legacy_commands


class Niantic(devices.common.legacy_commands.LegacyCommands):
    """The class overrides and provides methods for controlling Niantic."""

    def __init__(self, port):
        """Constructor for Niantic"""
        self.phy_type = None

        super(Niantic, self).__init__(port)

        self.codename = 'Niantic'
        self.interface = 'hss'
        self.snr_type = ['SNR']
        self.snr_unit_of_measure = ''
        self.tap = 1

    def ethspy_lane_get_status(self, lane):
        """Get the lane status and return it.
        
        Args:
            lane (): Unused, for compatibility only.

        Returns:
            dict: The current lane status.
        """
        return {'OUTPUT': 'N/A'}

    def ethspy_link_get_status(self):
        """Query the link status and return the results.
        
        Returns:
            dict: The current link status.
        """
        output = self.dictify(self.port.execute('hostCommand STATUS'))

        try:
            if output['LINK'] == 'UP':
                output['LINK-UP'] = True
            else:
                output['LINK-UP'] = False
        except KeyError:
            print('Warning: Could not get LINK-UP status. Setting to False.')
            output['LINK-UP'] = False

        return output

    def ethspy_rx_get_snr(self, abort, lane):
        """Get the SNR from Niantic and return it.
        
        Args:
            abort (int): Unused, for compatibility only.
            lane (int): Unused, for compatibility only.

        Returns:
            dict: The SNR.
        """
        output = self.dictify(self.port.execute('hostCommand SNR'))

        return output

    def ethspy_rx_get_status(self, lane):
        """Query the Rx status and return the results.
        
        Args:
            lane (int): The lane to run the command on.

        Returns:
            dict: The current Rx status.
        """
        rx_status = {}
        rx_status.update(
            self.dictify(self.port.execute('hostCommand STATUS RXFFE'))
        )
        rx_status.update(
            self.dictify(self.port.execute('hostCommand STATUS RXDFE'))
        )
        rx_status.update(
            self.dictify(self.port.execute('hostCommand STATUS RXTDFE'))
        )

        return rx_status

    def ethspy_summary_get_status(self):
        """Get the status summary and return it.
        
        Returns:
            dict: The summary of the current status.
        """
        summary = {}
        summary.update(self.dictify(self.port.execute('hostCommand STATUS')))
        summary.update(self.dictify(self.port.execute('hostCommand INFOLIST')))

        return summary

    def ethspy_tx_get_status(self, lane):
        """Query the Tx status and return the results.
        
        Args:
            lane (int): The lane to run the command on.

        Returns:
            dict: The current Tx status.
        """
        return self.dictify(self.port.execute('hostCommand STATUS TXFFE'))

    def get_coeffs(self, lane=-1):
        """Query the currently set coefficeints and return them.
        
        Niantic only supports SFI, and thus only one lane. 
        The lane is defaulted to zero.
        
        Args:
            lane (int): Unused, for compatibility only.

        Returns:
            dict: The currently set coefficients.
        """
        # NNT uses the STATUS TXFFE command to read the coeffs instead of HSS
        output = self.dictify(self.port.execute('hostCommand STATUS TXFFE'))

        try:
            output_dict = {
                0: {
                    'CM1': output['KR Final Coef_Minus_1'],
                    'C0': output['KR Final Coef_0'],
                    'C1': output['KR Final Coef_1']
                }
            }
        except ValueError:
            raise ethspylib.EthSpyError(
                'Error: Could not retrieve coefficients '
                'from the DUT. Ending script!'
            )

        return output_dict

    def get_initial_coeffs(self, lane=-1):
        init_coeffs = self.get_coeffs(lane)

        return init_coeffs

    @staticmethod
    def ethspy_module_info_get_all():
        return {'VENDOR NAME': 'Unspecified', 'VENDOR PN': 'Unspecified'}

