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


class Fortville25(devices.common.ethspy_commands.EthSpyCommands):
    """This class overrides and provides methods specific to Fortville25."""

    def __init__(self, port):
        """Constructor for Fortville25"""
        self.phy_type = 'UNVL'

        super(Fortville25, self).__init__(port)

        self.codename = 'Fortville25'
        self.interface = 'hss'
        self.snr_type = ['EYE-HEIGHT']
        self.snr_unit_of_measure = ' (mV)'
        self.tap = -1

        self.tap_settings = [
            [0, 0, 0, 'tap0'],
            [-3, 9, -15, 'tap1'],
            [-1, 10, -15, 'tap2'],
            [-3, 9, -15, 'tap3'],
            [-3, 8, -15, 'tap4'],
            [-3, 9, -15, 'tap5'],
            [-3, 10, -13, 'tap6'],
            [-3, 9, -15, 'tap7'],
            [0, 17, -15, 'tap8'],
            [-12, 15, 0, 'tap9']
        ]

        self.caui_coeffs = [[0, 0, 0]]

    def ethspy_lane_get_status(self, lane):
        """This method returns {'OUTPUT': 'N/A'} for compatibility.
        
        Args:
            lane (int): (Unused, for compatibility only.)

        Returns:
            dict: {'OUTPUT': 'N/A'}
        """
        return {'OUTPUT': 'N/A'}

    def ethspy_rx_get_snr(self, abort, lane, e_phy=True):
        """Get the VOM from UNVL and return it.
        
        Args:
            abort (int): (Unused, for compatibility only.)
            lane (int): The lane to retirieve the VOM from.
            e_phy (bool): If True, get the VOM from the external phy.

        Returns:
            dict: The VOM from the specified lane.
        """
        print('Getting the VOM. This may take a few seconds...')
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

    def get_coeffs(self, lane=0, e_phy=True):
        """Query the current coefficients and return them.
        
        Fortville25 only has one lane so it is defaulted to zero, it doesn't 
        matter what is passed in. The return dictionary is organized by lane.

        Args:
            lane (int): (Unused, for compatibility only)
            e_phy (bool): If True, get coefficients from the external phy

        Returns:
            dict: The currently set coefficients.
        """
        if e_phy:
            try:
                coeffs = json.loads(
                    self.port.execute(
                        'hostCommand ETHSPY TX GET-STATUS PHY:{} SIDE:LINE 0'.format(
                            self.phy_type
                        )
                    )
                )
            except ValueError:
                coeffs = {}

            try:
                output_dict = {
                    0: {
                        'LANE': 0,
                        'MODE': "SFI10G",
                        "CM1": coeffs['FINAL-CM1'],
                        'C0': coeffs['FINAL-C0'],
                        'C1': coeffs['FINAL-C1']
                    }
                }
            except KeyError:
                raise ethspylib.EthSpyError(
                    'Error: Could not retrieve coefficients from '
                    'the DUT. Ending script!'
                )
        else:
            output_dict = self.fvl.get_coeffs(lane)

        return output_dict

    def get_initial_coeffs(self, lane):
        """Get the initial coeffs from the Fortville25 device.

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

        print('TEST: Disabling link firmware management...')
        self.firmware_management_control('OFF')

        ethspylib.message_box(ethspylib.MESSAGE_BOX_INFO, title, hcb_text)

        return initial_coeffs

    def set_external_phy(self, e_phy):
        if e_phy:
            self.port.execute('SETPHY {}'.format(self.phy_type))
        elif not e_phy:
            self.port.execute('SETPHY TAMAR_FVL')
        else:
            print(
                'Warning: Incorrect value passed to '
                'set_external_phy(). Not set!'
            )

        return

    def hss(self, mode=None, pattern=None, lane=0, cm1=None, c0=None, c1=None):
        """Control the high-speed serial output of Fortville25.
        
        All of the arguments are optional. 
        If any are left out, they will not be changed.
        
        Args:
            mode (str): The mode to set the DUT into.
            pattern (str): The output pattern, SQUARE8, SQUARE1, PRBS9, PRBS31.
            lane (int): The lane to set.
            cm1 (int): The pre-cursor value.
            c0 (int): The cursor value.
            c1 (int): The post-cursor value.

        Returns:
            dict: The newly set coefficients.
        """
        print('\nDUT: Running the HSS command...')

        mode_dict = {'SFI10G': 'P10KN-P10LN', '25GBASE_SR': 'P40KN-P25LR'}

        if mode in mode_dict:
            self.port.execute(
                'hostCommand ETHSPY LINK SET-PMD PHY:{} {}'.format(
                    self.phy_type, mode_dict[mode]
                )
            )

        cmd_stub = 'hostCommand ETHSPY TX SET-TXFFE-FORCE PHY:{} L:{} {}'
        for c, stub in zip([cm1, c0, c1], ['CM1:{}', 'C0:{}', 'C1:{}']):
            if c is not None:
                self.port.execute(
                    cmd_stub.format(self.phy_type, lane, stub.format(c))
                )

        if pattern in ['PRBS9', 'PRBS31', 'SQUARE8', 'SQUARE1']:
            self.delete_adapter()   # Still required as of 09-Jan-2018
            self.add_adapter()      # Still required as of 09-Jan-2018

            # Still required as of 09-Jan-2018
            for i in range(0, 3):
                self.port.execute(
                    'hostCommand ETHSPY TX SET-PATTERN PHY:{} {} {}'.format(
                        self.phy_type, lane, pattern
                    )
                )
                time.sleep(0.25)

        coeffs = self.get_coeffs(lane)

        return coeffs
