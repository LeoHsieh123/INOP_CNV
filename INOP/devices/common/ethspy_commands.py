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
import json
from . import legacy_commands
import string
import time


class EthSpyCommands(legacy_commands.LegacyCommands):
    """This class provides access to the EthAgent ETHSPY command set.
    
    This class cannot be used on its own. A subclass should be used instead.
    """

    def __init__(self, port):
        """Constructor for EthSpyCommands"""
        super(EthSpyCommands, self).__init__(port)
        self.lanes = 1

        self.mode_translator = {
            'SFI': 'SFI10G',
            'XLPPI': 'XLPPI',
            'CR4/KR4': 'CR4'
        }

    def bandwidth(self):
        """Get the current bandwidth from the device."""
        try:
            output = json.loads(
                self.port.execute('hostCommand ETHSPY LINK GET-BANDWIDTH')
            )
        except ValueError:
            output = {}

        return output

    def coeff_file(self, coeffs, lane):
        """Base class method is needed so we can call it regardless of the DUT.
        
        This method is overridden by the :meth:`FVL.coeff_file` and
        :meth:`RRC.coeff_file` methods.
        
        Args:
            coeffs (dict): The coeffs to write to the file
            lane (int): The lane to write the coeffs for

        Returns:

        """
        pass

    def decrease_amplitude(self, lane):
        """Calculate and apply a new main cursor (C0) value to decrease the amplitude.

        A check is performed to make sure that the current C0 value is greater zero. If it is, the
        value is decremented. If it is not, nothing is changed and the current C0 value is
        returned.

        :param int lane: The DUT lane to decrement C0
        :return: The updated C0 value and a limit flag
        :rtype: tuple
        """
        coeffs = self.get_coeffs(lane)  # Get the current coefficients

        if int(coeffs[lane]['C0']) != 0:  # Check to make sure decrementing won't break anything
            new_c0 = coeffs[lane]['C0'] - self.tap  # Decrement the main tap
            self.hss(lane=lane, c0=new_c0)  # Run the new C0 value
            limit_flag = False
        else:
            new_c0 = coeffs[lane]['C0']  # Don't do anything if amplitude is 0
            limit_flag = True

        return new_c0, limit_flag

    def decrease_post(self, lane):
        coeffs = self.get_coeffs(lane)  # Get the current coefficients

        if coeffs[lane]['C1'] > 0:
            new_c1 = coeffs[lane]['C1'] - 1  # Decrease the post-cursor by subtracting 1
            self.hss(lane=lane, c1=new_c1)  # Run the new C1 value
            limit_flag = False
        else:
            new_c1 = coeffs[lane]['C1']  # Don't do anything if C1 is already at 0
            limit_flag = True

        return new_c1, limit_flag

    def decrease_pre(self, lane):
        coeffs = self.get_coeffs(lane)  # Get the current coefficients

        if coeffs[lane]['CM1'] > 0:
            new_cm1 = coeffs[lane]['CM1'] - 1  # Decrease the pre-cursor by subtracting 1
            self.hss(lane=lane, cm1=new_cm1)  # Run the new Cm1 value
            limit_flag = False
        else:
            new_cm1 = coeffs[lane]['CM1']  # Don't do anything if Cm1 is already at 0
            limit_flag = True

        return new_cm1, limit_flag

    def ethspy_lane_get_status(self, lane):
        """Run the ETHSPY LANE GET-STATUS command, convert it to a Python dictionary, and return it.

        :return: Output of the command
        :rtype: dict
        """
        try:
            output = json.loads(
                self.port.execute(
                    'hostCommand ETHSPY LANE GET-STATUS {}'.format(lane)
                )
            )
        except ValueError:
            output = {}

        return output

    def ethspy_link_get_stats(self):
        """Run the ETHSPY LINK GET-STATS command, convert it to Python dictionary, and return it.

        :return: Output of the command
        :rtype: dict
        """
        try:
            stats_output = json.loads(
                self.port.execute('hostCommand ETHSPY LINK GET-STATS')
            )
            good_rx, rx_errors = self.get_qr_counter()
            stats_output['QR-GOOD-RECEIVES'] = good_rx
            stats_output['QR-RECEIVE-ERRORS'] = rx_errors
        except ValueError:
            print('Could not get or convert output '
                   'from ETHSPY LINK GET-STATS command!')
            stats_output = {}

        return stats_output

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

    def ethspy_link_get_ttl(self):
        """Get the time-to-link (TTL) and return the results.
        
        Returns:
            dict: The TTL results
        """
        try:
            output = json.loads(
                self.port.execute(
                    'hostCommand ETHSPY LINK GET-TTL PHY:{} SIDE:LINE T:25000'.format(
                        self.phy_type
                    )
                )
            )
        except ValueError:
            print('Warning: Could not parse TTL output!')
            output = {}

        return output

    def ethspy_module_info_get_all(self):
        """Read the EEPROM in the SFP+ module and return the information.

        The output will have all characters that are not ASCII numbers,
        letters or ._-() removed for compatibility.

        Returns:
            dict: The SFP+ EEPROM contents.
        """
        raw_data = self.port.execute('hostCommand ETHSPY MODULE-INFO GET-ALL')

        time.sleep(10)

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
                    'hostCommand ETHSPY RX GET-STATUS PHY:{} SIDE:LINE {}'.format(
                        self.phy_type, lane
                    )
                )
            )
        except ValueError:
            output = {}

        return output

    def ethspy_summary_get_status(self):
        """Run the ETHSPY SUMMARY GET-STATUS command, convert it to a Python dictionary, and return it.

        :return: Output of the command
        :rtype: dict
        """
        try:
            output = json.loads(
                self.port.execute('hostCommand ETHSPY SUMMARY GET-STATUS')
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
                self.port.execute(
                    'hostCommand ETHSPY TX GET-STATUS %s' % lane
                )
            )
        except ValueError:
            output = {}

        return output

    def get_coeffs(self, lane=-1):
        """Get the currently set coefficients and return them as a dictionary.

        It is recommended to always call this method with a lane argument... behavior is not well
        defined otherwise. The output dictionary is formatted as LANE keys with a dictionary
        containing the coefficients as the value.

        :param int lane: The lane to get the coefficients from
        :return: The currently set coefficients
        :rtype: dict

        This method is overridden by :meth:`BDX.get_coeffs`, :meth:`FVL.get_coeffs`,
        :meth:`LBG.get_coeffs`, and :meth:`NNT.get_coeffs`.
        """
        output_dict = {}

        if lane == -1:
            output = self.dictify(self.port.execute('hostCommand HSS'))
        else:
            output = self.dictify(self.port.execute('hostCommand HSS LANE:%s' % lane))

        try:
            output_dict[int(output['LANE'])] = output
        except KeyError:
            pass

        return output_dict

    def get_firmware_revision(self):
        """Get the firmware revision number and return it.

        Returns:
            str: The firmware revision number (if available), N/A otherwise.
        """
        output = self.ethspy_summary_get_status()

        if 'FIRMWARE-REVISION' in output:
            r = output['FIRMWARE-REVISION']
        else:
            r = 'N/A'

        return r

    def get_initial_coeffs(self, lane=-1):
        init_coeffs = self.get_coeffs(lane)

        return init_coeffs

    def get_nvm_version(self):
        """Get the NVM version and return it.

        Returns:
            str: The NVM version number (is available), N/A otherwise.
        """
        output = self.ethspy_summary_get_status()

        if 'NVM-REVISION' in output:
            r = output['NVM-REVISION']
        else:
            r = 'N/A'

        return r

    def get_speed(self, ea_input=-1):
        """Extract the device speed from the "STATUS" command and return it.

        You can pass in the output from :meth:`DUT.status` and it will extract the speed from the
        output. If you do not pass anything in, it will run the STATUS command for you and return
        the speed.

        :param str ea_input: The output from the :meth:`DUT.status` method
        :return: The device speed
        :rtype: int
        :raises EthSpyError: if it could not extract the device speed
        """
        try:
            self.speed = self.ethspy_link_get_status()['CURRENT-LINK-SPEED']
        except KeyError:
            self.speed = 'ERROR'

        return self.speed

    def increase_amplitude(self, lane):
        """Calculate and apply a new main cursor (C0) value to increase the amplitude.

        A check is performed to make sure the sum of the taps is less than 63.
        If this check passes, the value is incremented. If it is not, nothing
        is changed and the current C0 value is returned.
        
        Args:
            lane (int): The DUT lane to increment C0

        Returns:
            int: The updated C0 value
        """
        coeffs = self.get_coeffs(lane)  # Get the current coefficients

        tap_sum = abs(coeffs[lane]['CM1']) + coeffs[lane]['C0'] + abs(coeffs[lane]['C1'])
        print('tap_sum = ', tap_sum)

        if tap_sum < 63:
            new_c0 = coeffs[lane]['C0'] + self.tap  # Increment the main tap
            print('new_c0 = ', new_c0)
            self.hss(lane=lane, c0=new_c0)  # Run the new C0 value
            limit_flag = False
        else:
            new_c0 = coeffs[lane]['C0']  # Don't do anything if tap_sum is greater than 63
            limit_flag = True

        return new_c0, limit_flag

    def increase_post(self, lane):
        coeffs = self.get_coeffs(lane)  # Get the current coefficients

        tap_sum = abs(coeffs[lane]['CM1']) + coeffs[lane]['C0'] + abs(coeffs[lane]['C1'])

        if tap_sum < 63:
            new_c1 = coeffs[lane]['C1'] + 1  # Increase the post-cursor by adding 1
            self.hss(lane=lane, c1=new_c1)  # Apply the new C1 value
            limit_flag = False
        else:
            new_c1 = coeffs[lane]['C1']  # Don't do anything if the tap_sum is greater than 63
            limit_flag = True

        return new_c1, limit_flag

    def increase_pre(self, lane):
        coeffs = self.get_coeffs(lane)  # Get the current coefficients

        tap_sum = abs(coeffs[lane]['CM1']) + coeffs[lane]['C0'] + abs(coeffs[lane]['C1'])

        if tap_sum < 63:
            new_cm1 = coeffs[lane]['CM1'] + 1  # Increase the pre-cursor by adding 1
            self.hss(lane=lane, cm1=new_cm1)  # Appky the new Cm1 value
            limit_flag = False
        else:
            new_cm1 = coeffs[lane]['CM1']  # Don't do anything if the tap_sum is greater than 63
            limit_flag = True

        return new_cm1, limit_flag

    # Deprecated methods???
    def get_link_status(self, ea_input=-1):
        """Extract the link status from the "STATUS" command and return it as a string.

        You can pass in the output from :meth:`DUT.status` and it will extract the link status from
        the output. If you do not pass anything in, it will run the STATUS command for you and
        return the link status.

        :param str ea_input: The output from the :meth:`DUT.status` method
        :return: UP or DOWN, the current link status of the device
        :rtype: str
        :raises EthSpyError: if it could not extract the link status
        """
        print('EthSpyCommands.get_link_status() is deprecated!')
        output = self.ethspy_link_get_status()

        try:
            if output['LINK-UP']:
                link = 'UP'
            else:
                link = 'DOWN'

        except KeyError:
            raise EthSpyError(
                'Could not get the link status from the DUT!\nMake sure it is '
                'connected and\\or the correct information was provided.\nEnding '
                'script!'
            )

        return link

    def get_module_info(self):
        """Read the EEPROM in the SFP+ module and return the values as a dictionary.

        The dictionary output will have the following keys:
        * module_type
        * module_vendor
        * module_part_number
        * module_compliance_code

        .. todo:: Add link to ETHSPY MODULE-INFO GET-ALL command documentation
        """
        print('EthSpyCommands.get_module_info() is deprecated!')
        data = self.port.execute('hostCommand ETHSPY MODULE-INFO GET-ALL')


        # filter now returns an iterator so it must be broken down
        data = [i for i in filter(string.printable.__contains__, data)]

        j_data = json.loads(data)
        for key in j_data:
            try:
                # Remove multiple whitespace characters
                j_data[key] = ' '.join(j_data[key].split())

                # Strip out characters that cause problems for filenames
                j_data[key] = ''.join(
                    [x if x.isalnum() or x in '._-()' else '_' for x in j_data[key]]
                )
            except (AttributeError, TypeError):
                pass

        return j_data

    def get_mac_port_number(self):
        print('EthSpyCommands.get_mac_port_number() is deprecated!')
        return 'N/A'

    def get_phy_port_number(self):
        print('EthSpyCommands.get_phy_port_number() is deprecated!')
        return 'N/A'

    def summary_get_status(self):
        """Run the ETHSPY SUMMARY GET-STATUS command, convert it to a Python dictionary, and return it.

        :return: Output of the command
        :rtype: dict
        """
        print('EthSpyCommands.summary_get_status() is deprecated!')
        return json.loads(
            self.port.execute('hostCommand ETHSPY SUMMARY GET-STATUS')
        )
