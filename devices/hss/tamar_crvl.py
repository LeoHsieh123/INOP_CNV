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
import time


class Tamar_CRVL(devices.common.ethspy_commands.EthSpyCommands):
    """This class overrides and provides methods specific to Fortville in Carlsville."""

    def __init__(self, port):
        """Constructor for Fortville in Carlsville"""
        self.phy_type = 'TAMAR_FVL'

        super(Tamar_CRVL, self).__init__(port)

        self.codename = 'Fortville'
        self.interface = 'hss'

        self.snr_type = ['VOM']

        self.snr_unit_of_measure = ' (mV)'
        
        self.lanes = 1

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
        """Query the tx status and return the results.

        Args:
            lane (int): The lane to run the command on.

        Returns:
            dict: The current tx status.
        """
        try:
            output = json.loads(
                self.port.execute(
                    'hostCommand ETHSPY TX GET-STATUS PHY:{} SIDE:LINE L:{}'.format(
                        self.phy_type, lane
                    )
                )
            )
        except ValueError:
            output = {}

        return output

    def ethspy_rx_get_snr(self, abort, lane=0):
        """
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
                    'hostCommand ETHSPY RX GET-VOM PHY:{} SIDE:LINE L:{}'.format(
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

    def get_coeffs(self, lane=-1):
        """Read the currently set coefficients and return them.

        If a lane is specified, return the currently set coefficients
            from that lane.
        If no lane is specified, return the coefficients currently set
            for all lanes.

        The return dictionary is organized by lane.

        Args:
            lane (int): The lane to retrieve the coefficients from (optional)

        Returns:
            dict: The currently set coefficients
        """
        coeff_dict = {}

        if lane != -1:
            hss_lane = json.loads(
                self.port.execute(
                    'hostCommand ETHSPY TX GET-STATUS PHY:{} SIDE:LINE L:{}'.format(
                        self.phy_type, lane)
                )
            )

            coeff_dict[lane] = {
                'LANE': lane,
                'CM1': hss_lane['OBSERVED-CM1'],
                'C0': hss_lane['OBSERVED-C0'],
                'C1': hss_lane['OBSERVED-C1']
            }

        else:
            for lane in range(0, 1):
                hss_lane = json.loads(
                    self.port.execute(
                        'hostCommand ETHSPY TX GET-STATUS PHY:{} SIDE:LINE L:{}'.format(
                            self.phy_type, lane)
                    )
                )
                coeff_dict[lane] = {
                    'LANE': lane,
                    'CM1': hss_lane['OBSERVED-CM1'],
                    'C0': hss_lane['OBSERVED-C0'],
                    'C1': hss_lane['OBSERVED-C1']
                }

        return coeff_dict

    def get_initial_coeffs(self, lane=-1):
        """Read the initial coefficients and return them.

        If a lane is specified, return the initial coefficients from that lane.
        If no lane is specified, return the initial coefficients for all lanes.

        The return dictionary is organized by lane.

        :param int lane: The lane to retrieve the coefficients from (optional)
        :return: initial coefficients
        :rtype: dict
        """
        initial_coeff_dict = {}

        if lane != -1:  # If a lane was passed in, then just run for that lane
            hss_lane = json.loads(
                self.port.execute(
                    'hostCommand ETHSPY TX GET-STATUS PHY:{} SIDE:LINE L:{}'.format(
                        self.phy_type, lane)
                )
            )
            initial_coeff_dict[lane] = {
                'LANE': lane,
                'CM1': hss_lane['INITIAL-CM1'],
                'C0': hss_lane['INITIAL-C0'],
                'C1': hss_lane['INITIAL-C1']
            }
        else:
            for lane in range(0, 1):
                try:
                    hss_lane = json.loads(self.port.execute(
                        'hostCommand ETHSPY TX GET-STATUS PHY:{} SIDE:LINE L:{}'.format(
                            self.phy_type, lane)))
                    initial_coeff_dict[lane] = {"LANE": lane,
                                                "CM1": hss_lane["INITIAL-CM1"],
                                                "C0": hss_lane["INITIAL-C0"],
                                                "C1": hss_lane["INITIAL-C1"]
                                                }
                except (KeyError, ValueError):
                    # If the hss_lane does not have a 'Lane' key, skip it
                    pass

        return initial_coeff_dict

    def hss(self, mode=None, pattern=None, lane=0, cm1=None, c0=None, c1=None):
        """Control the high-speed serial output of Fortville in Carlsville.

        All of the arguments are required.

        1. 'ETHSPY LINK ENABLE-LINK-MANAGEMENT EN:FALSE'
        2. 'ETHSPY TX SET-PATTERN L: SPD: PAT: '
        3. 'ETHSPY TX SET-TXFFE-FORCE L: CM1: C0: C1:'

        Args:
            mode (str): The mode to set the DUT into.
            pattern (str): The output pattern, SQUARE8, PRBS9, PRBS31.
            lane (int): The lane to set.
            cm1 (int): The pre1-cursor value.
            c0 (int): The cursor value.
            c1 (int): The post-cursor value.

        Returns:
            dict: The newly set coefficients.
        """
        print('\nDUT: Running the HSS command...')

        self.port.execute(
            'hostCommand ETHSPY LINK ENABLE-LINK-MANAGEMENT EN:FALSE'
        )
        mode_dict = {'SFI10G': '10G-SFI'}
        if mode in ['SFI10G'] and pattern is not None:
            self.port.execute(
                'hostCommand ETHSPY TX SET-PATTERN PHY:{} L:{} SPD:{} PAT:{}'.format(
                    self.phy_type, lane, mode_dict[mode], pattern
                )
            )

        if cm1 is not None and c0 is not None and c1 is not None:
            self.port.execute(
                'hostCommand ETHSPY TX SET-TXFFE-FORCE PHY:{} L:{} CM1:{} C0:{} C1:{}'.format(
                    self.phy_type, lane, cm1, c0, c1
                )
            )

        coeffs = self.get_coeffs(lane)

        return coeffs

    @staticmethod
    def ethspy_module_info_get_all():
        return {'VENDOR NAME': 'Unspecified', 'VENDOR PN': 'Unspecified'}