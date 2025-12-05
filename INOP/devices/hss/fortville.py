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
import os


class Fortville(devices.common.ethspy_commands.EthSpyCommands):
    """This class overrides and provides methods specific to Fortville."""

    def __init__(self, port):
        """Constructor for Fortville"""
        self.phy_type = 'TAMAR_FVL'

        super(Fortville, self).__init__(port)

        self.codename = 'Fortville'
        self.interface = 'hss'
        self.snr_type = ['VOM']
        self.snr_unit_of_measure = ' (mV)'
        self.tap = 1

        self.lanes = self.infer_lanes(self.get_speed())

    def adminq_control(self, state):
        """Control the state of the AdminQ in Fortville.
        
        Args:
            state (str): "ON" or "OFF" (case insensitive).

        Returns:
            str: The raw EthAgent output of the command.
        
        Raises:
            EthSpyError: If state is not "ON" or "OFF".
        """
        state = state.upper()
        if state == 'ON' or state == 'OFF':
            first_string = self.port.execute('hostCommand ADMINQ %s' % state)
            second_string = self.port.execute(
                'hostCommand ADMINQ MANAGE %s' % state
            )
        else:
            raise EthSpyError(
                'Incorrect value passed to FVL.adminq_control()!\n'
                'Only "ON" or "OFF" is allowed, but %s was sent!\n'
                'Ending script!' % state
            )

        return first_string, second_string

    def ethspy_rx_get_snr(self, abort, lane):
        """Get the VOM from Fortville and return it.
        
        Args:
            abort (int): (Unused, for compatibility only.)
            lane (int): The lane to retrieve the VOM from.

        Returns:
            float: The VOM value.
        """
        try:
            output = json.loads(
                self.port.execute(
                    'hostCommand ETHSPY RX GET-VOM {}'.format(lane)
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
                    'hostCommand ETHSPY TX GET-STATUS {}'.format(lane)
                )
            )

            coeff_dict[lane] = {
                'LANE': lane,
                'CM1': hss_lane['FINAL-CM1'],
                'C0': hss_lane['FINAL-C0'],
                'C1': hss_lane['FINAL-C1']
            }

            try:
                coeff_dict[lane]['MODE'] = self.mode_translator[
                    hss_lane['PCS-TYPE']
                ]
            except KeyError:
                coeff_dict[lane]['MODE'] = hss_lane['PCS-TYPE']
        else:
            for lane in range(0, 4):
                hss_lane = json.loads(
                    self.port.execute(
                        'hostCommand ETHSPY TX GET-STATUS {}'.format(lane)
                    )
                )
                coeff_dict[lane] = {
                    'LANE': lane,
                    'CM1': hss_lane['FINAL-CM1'],
                    'C0': hss_lane['FINAL-C0'],
                    'C1': hss_lane['FINAL-C1']
                }
                try:
                    coeff_dict[lane]['MODE'] = self.mode_translator[
                        hss_lane['PCS-TYPE']
                    ]
                except KeyError:
                    coeff_dict[lane]['MODE'] = hss_lane['PCS-TYPE']

        return coeff_dict

    def coeff_file(self, coeffs, lane):
        """Write coefficients to a file for later creation of a NVM image.
        
        The general format of the file is:
            {'tech':'da', 'lane':4, 'cm1':0, 'c0':37, 'cp1':1}
            {'tech':'sfi', 'lane':4, 'cm1':0, 'c0':37, 'cp1':1}

        Args:
            coeffs (dict): A dictionary containing the coeffs, ordered by lane
            lane (int): The logical lane of the coefficients to write
        """
        lane_stats = json.loads(
            self.port.execute('hostCommand ETHSPY LANE GET-STATUS %s' % lane)
        )
        p_lane = lane_stats['SUMMARY'][str(lane)]['PHYSICAL-LANE']

        f_name = os.path.join(
            _ETHSPY_VARS['OUTPUT_DIR'],
            '%s_EMPR_Custom_Coefficients.txt' % _ETHSPY_VARS['DUT_NAME']
        )

        # Write each line to the EMPR file
        with open(f_name, 'a') as empr:
            empr.write(
                "{'tech':'da', 'lane':%s, 'cm1':%s, 'c0':%s, 'cp1':%s}\n" % (
                    p_lane,
                    abs(coeffs[lane]['CM1']),
                    abs(coeffs[lane]['C0']),
                    abs(coeffs[lane]['C1'])
                )
            )

            empr.write(
                "{'tech':'sfi', 'lane':%s, 'cm1':%s, 'c0':%s, 'cp1':%s}\n" % (
                    p_lane,
                    abs(coeffs[lane]['CM1']),
                    abs(coeffs[lane]['C0']),
                    abs(coeffs[lane]['C1'])
                )
            )

        return

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
                    'hostCommand ETHSPY TX GET-STATUS {}'.format(lane)
                )
            )
            initial_coeff_dict[lane] = {
                'LANE': lane,
                'CM1': hss_lane['INITIAL-CM1'],
                'C0': hss_lane['INITIAL-C0'],
                'C1': hss_lane['INITIAL-C1']
            }

            try:
                initial_coeff_dict[lane]['MODE'] = self.mode_translator[
                    hss_lane['PCS-TYPE']
                ]
            except KeyError:
                initial_coeff_dict[lane]['MODE'] = hss_lane['PCS-TYPE']
        else:
            for lane in range(0, 4):
                try:
                    hss_lane = json.loads(self.port.execute(
                                              "hostCommand ETHSPY TX GET-STATUS %s" % lane))
                    initial_coeff_dict[lane] = {"LANE": lane,
                                                "MODE": self.mode_translator[hss_lane["PCS-TYPE"]],
                                                "CM1": hss_lane["INITIAL-CM1"],
                                                "C0": hss_lane["INITIAL-C0"],
                                                "C1": hss_lane["INITIAL-C1"]
                                                }
                except (KeyError, ValueError):
                    # If the hss_lane does not have a 'Lane' key, skip it
                    pass

        return initial_coeff_dict

    def hss(self, mode=-1, pattern=-1, lane=-1, cm1=None, c0=None, c1=None):
        """Control the high-speed serial output.

        All of the arguments are optional. If any are left out, they will not be changed.

        :param str mode: The mode to set the DUT into
        :param str pattern: The pattern to output, (SQUARE8, SQUARE1, PRBS9, PRBS31)
        :param int lane: The lane to set
        :param int cm1: The pre-cursor value
        :param int c0: The cursor value
        :param int c1: The post-cursor value
        :return: The newly set coefficients
        :rtype: dict
        """
        print('\nDUT: Running the HSS command...')

        mode_dict = {'SFI10G': 'SFI', 'XLPPI': 'XLPPI', 'CR4': 'CR4'}
        speed_dict = {'SFI10G': '10GS', 'XLPPI': '40GP', 'CR4': '40GP'}
        pattern_translator = {
            'PRBS9': 'SFI10G-PRBS9',
            'PRBS31': 'SFI10G-PRBS31',
            'SQUARE8': 'SFI10G-SQUARE8'
        }

        if mode in ['SFI10G', 'XLPPI', 'CR4']:
            self.port.execute('hostCommand ETHSPY LINK AUTO-NEG-ENABLED FALSE')
            self.port.execute(
                'hostCommand ETHSPY LINK SET-PMD {}'.format(mode_dict[mode])
            )
            self.port.execute(
                'hostCommand ETHSPY LINK SET-CURRENT-SPEED {}'.format(
                    speed_dict[mode]
                )
            )
            self.port.execute('hostCommand ETHSPY LINK PCS-ENABLED TRUE')

        if cm1 is not None:
            self.port.execute(
                'hostCommand ETHSPY TX SET-TXFFE-FORCE L:{} CM1:{}'.format(
                    lane, cm1
                )
            )

        if c0 is not None:
            self.port.execute(
                'hostCommand ETHSPY TX SET-TXFFE-FORCE L:{} C0:{}'.format(
                    lane, c0
                )
            )

        if c1 is not None:
            self.port.execute(
                'hostCommand ETHSPY TX SET-TXFFE-FORCE L:{} C1:{}'.format(
                    lane, c1
                )
            )

        if pattern in pattern_translator:
            self.port.execute(
                'hostCommand ETHSPY TX SET-PATTERN {} {}-{}'.format(
                    lane, mode, pattern
                )
            )

        self.port.execute(
            'hostCommand ETHSPY TX ENABLE-TXFFE-FORCE {} TRUE'.format(lane)
        )
        coeffs = self.get_coeffs(lane)

        return coeffs
