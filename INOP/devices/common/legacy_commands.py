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
# Standard library imports
import ast

# Local project imports
import ethspylib


class LegacyCommands(object):
    """This class provides access to the legacy EthAgent commands."""

    def __init__(self, port):
        """Constructor for LegacyCommands"""
        self.port = port

        infolist = self.infolist()
        self.branding_string = infolist['BRANDING_STRING']
        self.device_id = infolist['DEVICE_ID']
        self.codename = infolist['CODENAME']
        self.interface = 'BASE'
        self.slot = infolist['SLOT']
        self.pcie_bdf = '{}:{}.{}'.format(
            infolist['BUS'], infolist['DEVICE'], infolist['FUNCTION']
        )

        self.speed = self.get_speed()

        show = self.show()
        self.mac_addr = self.get_mac_addr(show)
        version = self.version()

        self.ea_version = version['ETHAGENT-VERSION']
        self.qv_version = version['QV-VERSION']

        self.host_name = self.port.host_name
        self.slot_number = self.port.slot_number

        #self.port.execute('hostCommand OverrideTCPTimeout 90000')

    def add_adapter(self):
        self.port.execute("hostCommand ADD %s" % self.slot_number)
        return

    def adminq_control(self, state):
        """This base class method is needed so we can call it regardless of the DUT.

        This method is overridden in the :meth:`FVL.adminq_control` method.

        :param str state: "ON" or "OFF"
        """
        pass

    def bandwidth(self):
        """Get the current bandwidth from the device."""
        try:
            # output = json.loads(
            #     self.port.execute('hostCommand ETHSPY LINK GET-BANDWIDTH')
            # )
            output = {'TX-MBPS': 0, 'RX-MBPS': 0}
        except ValueError:
            output = {}

        return output

    def blink(self):
        """Blink the specified slot."""
        self.port.execute('hostCommand BLINK')

        return

    def clear_counters(self):
        """Clear the Tx/Rx receive counters."""
        self.port.execute("hostCommand HC")

        return

    def close(self):
        """Close the connection to the device.
        
        The TCP timeout is reset when this method is called.
        """
        self.port.execute('hostCommand ResetTCPTimeoutToDefault')
        self.port.close()
        return

    def firmware_management_control(self, state):
        state = state.upper()
        if state == 'ON' or state == 'OFF':
            return_string = self.port.execute(
                'hostCommand ADMINQ MANAGE {}'.format(state)
            )
        else:
            raise ethspylib.EthSpyError(
                'Incorrect value passed to '
                'LegacyCommands.firmware_management_control()!\n'
                'Only "ON" or "OFF" is allowed, but {} was sent!\n'
                'Ending script!'.format(state)
            )

        return return_string

    def get_mac_addr(self, ea_input=-1):
        """Extract the MAC address of the device from the "SHOW" command and return it as a string.

        You can pass in the output from :meth:`DUT.show` and it will extract the MAC address from
        the output. If you do not pass anything in, it will run the SHOW command for you and return
        the MAC address.

        :param str ea_input: The output from the :meth:`DUT.show` method
        :return: The MAC address of the device
        :rtype: str
        :raises EthSpyError: if it could not extract the MAC address
        """
        if ea_input == -1:
            ea_input = self.dictify(self.show())
        else:
            ea_input = self.dictify(ea_input)
        # print(ea_input)
        try:
            address = ea_input['ETHERNET ADDRESS']
            self.mac_addr = address.strip(' DESTINATION ADDRESS')
        except KeyError:
            raise EthSpyError('''Could not get the MAC address from the DUT!
            Make sure it is connected and\or the correct information was provided.
            Ending script!''')

        return self.mac_addr

    def get_qr_counter(self, decimal=True):
        """Get the receive counters and return the desired type of values.
        
        If <decimal> is True, return the decimal values, otherwise return the 
            hex values.
        
        Returns:
            tuple: Good receives, receive errors
        """
        qr_tokens = self.qr().split()

        if decimal:
            good_receives = int(qr_tokens[1].strip('d'))
            receive_errors = int(qr_tokens[3].strip('d'))
        else:
            good_receives = int(qr_tokens[0].strip('X'))
            receive_errors = int(qr_tokens[2].strip('X'))

        return good_receives, receive_errors

    def get_qt_counter(self, decimal=True):
        """Get the transmit counters and return the desired type of values.

        If <decimal> is True, return the decimal values, otherwise return the 
            hex values.

        Returns:
            tuple: Good transmits, transmit errors
        """
        qt_tokens = self.qt().split()

        if decimal:
            good_transmits = int(qt_tokens[1].strip('d'))
            transmit_errors = int(qt_tokens[3].strip('d'))
        else:
            good_transmits = int(qt_tokens[0].strip('X'))
            transmit_errors = int(qt_tokens[2].strip('X'))

        return good_transmits, transmit_errors

    def get_slot(self, ea_input=-1):
        """Extract the slot number from the INFOLIST command and return it.

        You can pass in the output from :meth:`DUT.infolist` and it will extract the slot number
        from the output. If you do not pass anything in, it will run the INFOLIST command for you
        and return the slot number.

        :param str ea_input: The output from the :meth:`DUT.infolist` method
        :return: The device slot number
        :rtype: int
        :raises EthSpyError: if it could not extract the device slot number
        """
        if ea_input == -1:
            ea_input = self.infolist()

        try:
            self.slot = ea_input['SLOT']
        except KeyError:
            raise EthSpyError('''Could not get the slot number from the DUT!
            Make sure it is connected and\or the correct information was provided.
            Ending script!''')

        return self.slot

    def get_speed(self):
        """Extract the device speed from the "STATUS" command and return it.

        You can pass in the output from :meth:`DUT.status` and it will extract the speed from the
        output. If you do not pass anything in, it will run the STATUS command for you and return
        the speed.

        :param str ea_input: The output from the :meth:`DUT.status` method
        :return: The device speed
        :rtype: int
        :raises EthSpyError: if it could not extract the device speed
        """
        output = self.dictify(self.port.execute('hostCommand STATUS'))
        try:
            if output['SPEED'] == 'NA':
                self.speed = 'NA'
                return self.speed
            self.speed = str(int(output['SPEED'])//1000) + 'G'
            if self.speed == '0G':
                self.speed = '100M'
            if self.speed == '2G':
                self.speed = '2.5G'
        except KeyError:
            self.speed = 'ERROR'

        return self.speed

    def get_ttl(self):
        """Run the time-to-link (TTL) command and return the results as a dictionary.

        Attempts to convert all values to floats, otherwise they are returned unchanged.

        :return: Formatted output from the TTL command
        :rtype: dictionary
        """
        output = self.dictify(self.port.execute('hostCommand TTL'))
        try:
            if output['Error'] == 'Please make sure link is up':
                print('TTL failure! Retrying...')
                output = self.get_ttl()
        except KeyError:
            for key, value in output.items():
                try:
                    output[key] = float(value)
                except (ValueError, TypeError):
                    output[key] = value

        clean_output = {}
        for key in output:
            if not output[key]:
                pass
            else:
                clean_output[key] = output[key]

        return clean_output

    def getstats(self, raw=False):
        """Run the GETSTATS command and return the raw output.
        
        If <raw> is False, the output is converted to a dictionary
            before being returned.
        
        Returns:
            str: The raw output of the GETSTATS command.
        """
        output = self.port.execute('hostCommand GETSTATS')

        if not raw:
            output = self.dictify(output)

        return output

    def hostinfo(self):
        """Gather info from the host system and return it.
        
        Returns:
            dict: The host system information.
        """
        try:
            output = ast.literal_eval(self.port.execute('hostCommand HOSTINFO'))
        except ValueError:
            output = {}

        return output

    def infolist(self, raw=False):
        """Run the INFOLIST command and return the raw output.
        
        Args:
            raw (bool): Return raw or formatted output.

        Returns:
            dict: The output of the INFOLIST command.
        """
        output = self.port.execute('hostCommand INFOLIST')

        if not raw:
            output = self.dictify(output)

        return output

    def list_phy(self, raw=False):
        """Run the LISTPHY command and return the output.
        
        Args:
            raw (bool): Return raw or formatted output.

        Returns:
            str: The output of the LISTPHY command.
        """
        output = self.port.execute('hostCommand LISTPHY')

        if not raw:
            output = self.dictify(output)

        return output

    def set_base_t_auto_neg(self, speed):
        """Change the auto-negotiation settings for Base-T devices.
        
        Notes:
            This is currently not working!!!
        
        Args:
            speed (str): The desired link speed
        """
        # TODO Fix this method! Does not seem to be properly changing the auto-neg.
        if speed == '10G':
            self.wmii('20', '1001', page_or_device=7)
        elif speed == '5G':
            self.wmii('20', '1', page_or_device=7)
            self.wmii('C400', '9853', page_or_device=7)
        elif speed == '2.5G':
            self.wmii('20', '1', page_or_device=7)
            self.wmii('C400', '9453', page_or_device=7)
        elif speed == '1G':
            self.wmii('20', '1', page_or_device=7)
            self.wmii('C400', '9053', page_or_device=7)
        else:
            print('Invalid speed setting!')

    def set_packet_size(self, speed, size):
        """Change the packet size to the desired length.

        Args:
            size (int): Value between 64 and 1522

        Returns:
            int: The packet size that was set
        """
        if size < 64:
            print('BER packet size of %s is out of range!' % size)
            print('Changing BER packet size to 64.')
            size = 64
        elif size > 1522:
            print('BER packet size of %s is out of range!' % size)
            print('Changing BER packet size to 1522.')
            size = 1522

        #self.port.execute('hostCommand T1 SPEED:{} SIZE:{}'.format(speed,size))
        self.port.execute('hostCommand T1 SIZE:{}'.format(size))

        return size

    def qr(self):
        """Run the QR command and return the raw output.
        
        Returns:
            str: The raw output of the QR command.
        """
        return self.port.execute('hostCommand QR')

    def qt(self):
        """Run the QT command and return the raw output.
        
        Returns:
            str: The raw output of the QT command.
        """
        return self.port.execute('hostCommand QT')

    def reep(self, start='0', stop='FF'):
        """Read the contents of the the EEPROM. Return the data as a raw string."""
        return self.port.execute('hostCommand REEP {} E:{}'.format(start, stop))

    def reset(self):
        """Reset the adapter."""
        self.port.execute('hostCommand RESET')

    def riosf(self, page, word):
        """Run the RIOSF command and return the raw output.

        Returns:
            str: The raw output of the RIOSF command.
        """
        return self.port.execute('hostCommand RIOSF {} {}'.format(page, word))

    def rmii(self, address, end_range=None, page=None, device=None, width=None):
        """Do a raw PHY register read over MDIO.
        
        Args:
            address (str): 
            end_range (str): 
            page (int): 
            device (int): 
            width (int): 

        Returns:
            str: The requested register contents.
        """
        if end_range is not None:
            end_string = ' E:{}'.format(end_range)
        else:
            end_string = ''

        if page is not None:
            page_string = ' P:{}'.format(page)
        else:
            page_string = ''

        if device is not None:
            device_string = ' D:{}'.format(device)
        else:
            device_string = ''

        if width is not None:
            width_string = ' W:{}'.format(width)
        else:
            width_string = ''

        output = self.port.execute(
            'hostCommand RMII {} {}{}{}{}'.format(
                address, end_string, page_string, device_string, width_string
            )
        )

        return output

    def show(self):
        """Run the SHOW command and return the raw output.
        
        Returns:
            str: The raw output of the SHOW command.
        """
        return self.port.execute('hostCommand SHOW')

    def status(self, raw=False):
        """Query the status.
        
        If <raw> is False, the output is converted to a dictionary
            before being returned.
        
        Returns:
            str: The current status.
        """
        output = self.port.execute('hostCommand STATUS')

        if not raw:
            output = self.dictify(output)

        return output

    def t1_speed(self, speed):
        """This method forces the speed.
        
        Args:
            speed (int): The desired speed

        Returns:
            int: The speed that was set.
        """
        self.port.execute('hostCommand T1 SPEED:{}'.format(speed))

        return speed

    def ttl(self, raw=False):
        """Run the time-to-link (TTL) command and return the raw output.
        
        If <raw> is False, the output is converted to a dictionary
            before being returned.
            
        Returns:
            dict: The TTL.
        """
        float_conversion_list = [
            'TRAIN COUNT',
            'AN COUNT',
            'AN TTL(MS)',
            'TRAIN TTL(MS)',
            'LINK TTL(MS)',
            'RESOLUTION(MS)',
            'TICK TIME(MS)',
            'CYCLES',
            'TIMEOUT',
            'CAL(MS)'
        ]

        output = self.port.execute('hostCommand TTL')

        if not raw:
            output = self.dictify(output)

            for item in float_conversion_list:
                if item in output:
                    output[item] = float(output[item])

        return output

    def tx_rx_control(self, switch):
        """Control the transmission of packets.
        
        Args:
            switch (str): "START" or "STOP" (case insensitive).

        Raises:
            EthSpyError: If something other than "START" or "STOP" is passed in
        """
        if switch.upper() == 'START':
            self.port.execute('hostCommand TX')
        elif switch.upper() == 'STOP':
            self.port.execute('hostCommand XX')
        else:
            raise EthSpyError(
                f'{switch} is not a valid argument to tx_rx_control()! Use START or STOP!'
                '\nEnding script!'
            )

        return

    def version(self, raw=False):
        """Get the EthAgent and QV version and return the raw output.
        
        Returns:
            str: The raw version output.
        """
        output = self.port.execute('hostCommand VER')

        if not raw:
            nl_split = output.split('\r\n')

            first_part = nl_split[0]
            first_split = first_part.split(' ')
            ea = first_split[-1]

            second_part = nl_split[1]
            second_split = second_part.split(' ')
            qv = second_split[-1]

            output = {'ETHAGENT-VERSION': ea, 'QV-VERSION': qv}

        return output

    def wmii(self, hex_address, hex_value, logical_phy=None, page_or_device=None):
        """Do a raw PHY register write over MDIO.
        
        Args:
            hex_address (str): 
            hex_value (str): 
            logical_phy (int): 
            page_or_device (int): 
        """
        if logical_phy:
            phy_string = ' P:{}'.format(logical_phy)
        else:
            phy_string = ''

        if page_or_device:
            page_string = ' D:{}'.format(page_or_device)
        else:
            page_string = ''

        self.port.execute(
            'hostCommand WMII {} {}{}{}'.format(
                hex_address, hex_value, phy_string, page_string
            )
        )

    @staticmethod
    def dict_to_list(lst, d):
        """Create a list of values by extracting from the dictionary the list of keys passed in.

        The order of the list is determined by the order of keys in lst.

        :param list lst: The keys to read from the dictionary
        :param dict d: The dictionary to extract values from
        :return: The device branding string
        :rtype: list
        :raises EthSpyError: if a key could not be found in the dictionary
        """
        output_list = []

        try:
            for val in lst:
                output_list.append(d[val])
        except KeyError:
            raise EthSpyError('Could not find %s in the output!' % d[val])

        return output_list

    @staticmethod
    def dictify(raw):
        """Create a dictionary from the EthAgent key-value pair output and return it.

        If the line has no colon, the string is put into the key and the value is set to None.
        The output (keys and values) will be all upper case.

        Args:
            raw (str): Raw EthAgent output

        Returns:
            dict: The EthAgent output processed into a dictionary, all upper case
        """
        raw = raw.upper()
        output = {}

        input_lines = raw.split('\n')

        for line in input_lines:
            line_sep = line.split(':')
            if len(line_sep) > 1:
                output[line_sep[0].strip()] = line_sep[1].strip()
            else:
                line_sep = line.split('=')
                if len(line_sep) > 1:
                    output[line_sep[0].strip()] = line_sep[1].strip()
                else:
                    output[line_sep[0].strip()] = None

        return output

    @staticmethod
    def infer_lanes(speed):
        if (speed == '40000') or (speed == '100000') or speed == '100G' or speed == '40GP':
            lanes = 4
        elif speed == '20000':
            lanes = 2
        elif speed == '10G' or speed == '25G':
            lanes = 1
        else:
            lanes = 1

        return lanes

    @staticmethod
    def nested_dict_to_list(key_lst, val_lst, d):
        """Extract values from a nested dictionary and return them in a list.

        val_list must contain a sub-list for each key in key_list.

        :param list key_lst: The keys to find in the nested dictionary
        :param list val_lst: The values to find under the corresponding keys
        :param dict d: The nested dictionary to extract values from
        :return: The specified values in a list
        :rtype: list
        """
        output_list = []

        for key, values in zip(key_lst, val_lst):
            for value in values:
                try:
                    output_list.append(d[key][value])
                except KeyError:
                    pass

        return output_list

    # Deprecated methods???
    def delete_adapter(self):
        print('LegacyCommands.delete_adapter() is deprecated!')
        self.port.execute("hostCommand DEL %s" % self.slot_number)
        return

    def get_branding_string(self, ea_input=-1):
        """Extract the branding string from the INFOLIST command and return it as a string.

        You can pass in the output from :meth:`DUT.infolist` and it will extract the branding
        string from the output. If you do not pass anything in, it will run the INFOLIST command
        for you and return the branding string.

        :param str ea_input: The output from the :meth:`DUT.infolist` method
        :return: The device branding string
        :rtype: str
        :raises EthSpyError: if it could not extract the device branding string
        """
        print('LegacyCommands.get_branding_string() is deprecated!')
        if ea_input == -1:
            ea_input = self.dictify(self.infolist())
        else:
            ea_input = self.dictify(ea_input)

        try:
            self.branding_string = ea_input['BRANDING_STRING']
        except KeyError:
            raise EthSpyError('''Could not get the branding string from the DUT!
            Make sure it is connected and\or the correct information was provided.
            Ending script!''')

        return self.branding_string

    def get_codename(self, ea_input=-1):
        """Extract the codename from the INFOLIST command and return it as a string.

        You can pass in the output from :meth:`DUT.infolist` and it will extract the codename from
        the output. If you do not pass anything in, it will run the INFOLIST command for you and
        return the codename.

        :param str ea_input: The output from the :meth:`DUT.infolist` method
        :return: The device codename
        :rtype: str
        :raises EthSpyError: if it could not extract the device codename
        """
        # print('LegacyCommands.get_codename() is deprecated!')
        if ea_input == -1:
            ea_input = self.infolist()
        else:
            ea_input = self.dictify(ea_input)

        try:
            self.codename = ea_input['CODENAME']
        except KeyError:
            raise EthSpyError('''Error: Could not get the codename from the DUT!
            Make sure it is connected and\or the correct information was provided.
            Ending script!''')

        return self.codename

    def get_device_id(self, ea_input=-1):
        """Extract the device ID from the INFOLIST command and return it as a string.

        You can pass in the output from :meth:`DUT.infolist` and it will extract the device ID from
        the output. If you do not pass anything in, it will run the INFOLIST command for you and
        return the device ID.

        :param str ea_input: The output from the :meth:`DUT.infolist` method
        :return: The device ID
        :rtype: str
        :raises EthSpyError: if it could not extract the device ID
        """
        print('LegacyCommands.get_device_id is deprecated!')
        if ea_input == -1:
            ea_input = self.dictify(self.infolist())
        else:
            ea_input = self.dictify(ea_input)

        try:
            self.dev_id = ea_input['DEVICE_ID']
        except KeyError:
            raise EthSpyError('''Could not get the device ID from the DUT!
            Make sure it is connected and\or the correct information was provided."
            Ending script!''')

        return self.dev_id

    def get_ea_version(self, ea_input=-1):
        """Extract the EthAgent version from the VER command and return it.

        You can pass in the output from :meth:`DUT.version` and it will extract the EthAgent
        version number from the output. If you do not pass anything in, it will run the INFOLIST
        command for you and return the EthAgent version number.

        :param str ea_input: The output from the :meth:`DUT.version` method
        :return: The EthAgent version number
        :rtype: str
        :raises EthSpyError: if it could not extract the EthAgent version
        """
        print('LegacyCommands.get_ea_version() is deprecated!')
        if ea_input == -1:
            ea_input = self.version()

        try:
            nl_split = ea_input.split('\r\n')
            first_part = nl_split[0]
            first_split = first_part.split(' ')
            ea_version = first_split[-1]
        except:
            raise EthSpyError('''Error parsing the VER output!
            Make sure it is connected and\or the correct information was provided.
            Ending script!''')

        return ea_version

    def get_hostname(self):
        """Get the host name of the DUT and return it as a string."""
        print('LegacyCommands.get_hostname() is deprecated!')
        return self.port.execute("hostCommand GetHostname")

    def get_link_mode(self, ea_input=-1):
        """Extract the link mode from the INFOLIST command and return it as a string.

        You can pass in the output from :meth:`DUT.infolist` and it will extract the link mode from
        the output. If you do not pass anything in, it will run the INFOLIST command for you and
        return the link mode.

        :param str ea_input: The output from the :meth:`DUT.infolist` method
        :return: The device link mode
        :rtype: str
        :raises EthSpyError: if it could not extract the device link mode
        """
        print('LegacyCommands.get_link_mode() is deprecated!')
        link_mode = None

        if ea_input == -1:
            ea_input = self.dictify(self.status())
        else:
            ea_input = self.dictify(ea_input)

        try:
            link_mode = ea_input['MODE']
        except KeyError:
            raise EthSpyError('''Could not get the link mode from the DUT!
            Make sure it is connected and\or the correct information was provided.
            Ending script!''')

        return link_mode

    def get_pcie(self, ea_input=-1):
        """Extract the PCIe Bus:Device.Function number from the "INFOLIST" command and return it.

        You can pass in the output from :meth:`DUT.infolist` and it will extract the BDF from the
        output. If you do not pass anything in, it will run the INFOLIST command for you and return
        the BDF.

        :param str ea_input: The output from the :meth:`DUT.infolist` method
        :return: The devices PCIe BDF formatted as Bus:Device.Function
        :rtype: str
        :raises EthSpyError: if it could not extract the PCIe Bus:Device.Function
        """
        print('LegacyCommands.get_pcie() is deprecated!')
        if ea_input == -1:
            ea_input = self.dictify(self.infolist())
        else:
            ea_input = self.dictify(ea_input)

        pcie = {}
        try:
            pcie['BUS'] = ea_input['BUS']
            pcie['DEVICE'] = ea_input['DEVICE']
            pcie['FUNCTION'] = ea_input['FUNCTION']
        except KeyError:
            raise EthSpyError('''Could not get the PCIe info from the DUT.
            Make sure it is connected and\or the correct information was provided.
            Ending script!''')

        return pcie

    def get_qv_version(self, ea_input=-1):
        """Extract the QV version from the EthAgent VER command and return it.

        You can pass in the output from :meth:`DUT.version` and it will extract the QV version
        number from the output. If you do not pass anything in, it will run the INFOLIST command
        for you and return the QV version number.

        :param str ea_input: The output from the :meth:`DUT.version` method
        :return: The QV version EthAgent is using
        :rtype: str
        :raises EthSpyError: if it could not extract the QV version
        """
        print('LegacyCommands.get_qv_version() is deprecated!')
        if ea_input == -1:
            ea_input = self.version()

        try:
            nl_split = ea_input.split('\r\n')
            second_part = nl_split[1]
            second_split = second_part.split(' ')
            qv_version = second_split[-1]
        except:
            raise EthSpyError('''Error parsing the VER output!\n Make sure it is connected and\or
            you passed the correct information to the DUT.get_qv_version() method.
            Ending script!''')

        return qv_version

    def update_vars(self):
        """Update the object variables that were set in the :meth:`DUT.__init__` method.

        This method updates the link_mode and speed object variables.
        It returns a dictionary with the following keys:
        * branding_string
        * codename
        * pcie
        * mac_addr
        * link_mode
        * speed
        * slot

        :returns: Updated variables that were set in the :meth:`DUT.__init__` method.
        :rtype: Dictionary
        """
        # self.info = self.infolist()
        # self.branding_string = self.get_branding_string(self.info)
        # self.codename = self.get_codename(self.info)
        # self.pcie = self.get_pcie(self.info)

        # self.mac_addr = self.get_mac_addr()
        print('LegacyCommands.update_vars() is deprecated!')
        self.status = self.status()
        self.link_mode = self.get_link_mode(self.status)
        self.speed = self.get_speed()

        # self.slot = self.get_slot()

        return {'branding_string': self.branding_string, 'codename': self.codename,
                'pcie': self.pcie, 'mac_addr': self.mac_addr, 'link_mode': self.link_mode,
                'speed': self.speed, 'slot': self.slot}

