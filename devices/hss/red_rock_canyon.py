import devices.common.legacy_commands
import ethspylib


class RedRockCanyon(devices.common.legacy_commands.LegacyCommands):
    """This class overrides and provides methods for controlling Red Rock Canyon."""

    def __init__(self, port):
        """Constructor for RedRockCanyon"""
        self.phy_type = None

        super(RedRockCanyon, self).__init__(port)

        self.codename = 'RedRockCanyon'
        self.interface = 'hss'
        self.snr_type = ['EHM']
        self.snr_unit_of_measure = ' (mV)'
        self.tap = -1

        # Initialize some constants for tuner.coefficient_tuning
        self.MAX_PRE = 10
        self.MAX_MAIN = 30
        self.MAX_POST = 10
        self.MAIN_LOW = 600e-3
        self.MAIN_HIGH = 640e-3

        # Set constants for CR4_40G testing
        self.TNPMLR_COEFFS = {'CM1': 0, 'C0': 0, 'C1': 0, 'tag': 'TNPMLR'}
        self.TNPMSR_COEFFS = {'CM1': 0, 'C0': 0, 'C1': 0, 'tag': 'TNPMSR'}

        self.LINEAR_PULSE_COEFFS = [{'CM1': 0, 'C0': 0, 'C1': 0, 'tag': 'ref'},
                                    {'CM1': 3, 'C0': 9, 'C1': 15, 'tag': 'init'},
                                    {'CM1': 0, 'C0': 11, 'C1': 21, 'tag': 'range_post'},
                                    {'CM1': 15, 'C0': 11, 'C1': 0, 'tag': 'range_pre'}]

        self.SWEEP_STEPS = [{'CM1': 3, 'C0': 9, 'C1': 15},
                            {'CM1': 3, 'C0': 9, 'C1': 13},
                            {'CM1': 3, 'C0': 9, 'C1': 11},
                            {'CM1': 1, 'C0': 9, 'C1': 15},
                            {'CM1': 5, 'C0': 9, 'C1': 15},
                            {'CM1': 3, 'C0': 7, 'C1': 15},
                            {'CM1': 3, 'C0': 5, 'C1': 15}]

        self.JITTER_COEFFS = {'CM1': 1, 'C0': 10, 'C1': 8, 'tag': 'jitter'}
        self.SQ8ORSQ10 = "sq08"

        self.tx_ready = False

        self.tap_settings = [
            [0, 0, 0, 'tap0'],
            [3, 9, 15, 'tap1'],
            [3, 10, 13, 'tap2'],
            [3, 8, 17, 'tap3'],
            [3, 8, 15, 'tap4'],
            [3, 10, 15, 'tap5'],
            [1, 10, 15, 'tap6'],
            [1, 8, 15, 'tap7'],
            [0, 10, 22, 'tap8'],
            [15, 10, 0, 'tap9']
        ]

        self.caui_coeffs = [0, 0, 0]

        self.slot_map = self.slot_to_port_mapping()
        return

    def get_snr(self, abort, lane=-1):
        """Get the eye height and return it.

        :param int lane: The lane to get the eye height from
        :return: The eye height
        :rtype: str

        .. warning:: **ALWAYS** pass in a lane to this method. Behavior is unspecified otherwise!

        .. todo:: Remove multi-lane capability and require that a lane always be provided. This
           will simplify the interface to this method.

        """
        if lane == -1:
            output = self.dictify(self.port.execute("hostCommand GETRXSTATUS"))
        else:
            output = self.dictify(self.port.execute("hostCommand GETRXSTATUS LANE:%s" % lane))

        return output["EYE_HEIGHT_MEASURE(mV)"]

    def hss(self, mode=-1, pattern=-1, lane=-1, cm1=-1, c0=-1, c1=-1):
        """Control the high-speed serial output of the device.

        All of the arguments are optional. If an argument is omitted, it will stay as the currently
        set value. Because RRC uses different mode strings, the mode value is converted.

        :param str mode: The mode to set the slot too, e.g. SFI10G, XLPPI, 40GBASE-CR4...
        :param str pattern: The pattern to output, e.g. PRBS9, PRBS31, SQUARE8, SQUARE1...
        :param int lane: The lane to be controlled
        :param int cm1: The pre-cursor value
        :param int c0: The main-cursor value
        :param int c1: The post-cursor value
        :return: The updated settings from EthAgent
        :rtype: dict

        .. note::
           For a complete list of values that can be used in the mode and pattern options, check
           the EthAgent documentation (link needs to be added here).

        .. todo:: Add link to EthAgent HSS command documentation.
        """

        print("\nSetting the DUT...")

        if mode == 'SFI10G':
            mode = '10GBASE_SR'
        elif mode == 'XLPPI':
            mode = '40GBASE_SR'
        elif mode == 'CR4':
            mode = '40GBASE_CR'

        # Put the values from the method call into a dict
        hss_vars = {'mode': mode, 'pattern': pattern, 'lane': lane, 'cm1': cm1, 'c0': c0, 'c1': c1}

        print("HSS MODE:%s PATTERN:%s LANE:%s CM1:%s C0:%s C1:%s\n" % (
            hss_vars['mode'], hss_vars['pattern'], hss_vars['lane'], hss_vars['cm1'],
            hss_vars['c0'], hss_vars['c1']))

        output = self.dictify(self.port.execute(
            "hostCommand HSS MODE:%s PATTERN:%s LANE:%s CM1:%s C0:%s C1:%s" % (
                hss_vars['mode'], hss_vars['pattern'], hss_vars['lane'], hss_vars['cm1'],
                hss_vars['c0'], hss_vars['c1'])))

        return output

    def tx_rx_control(self, switch):
        """Check to ensure Tx has been manually set up, then call :meth:`DUT.tx_rx_control`.
        
        Args:
            switch (str): "START" or "STOP"
        """
        # We don't want to make the user setup Tx/Rx
        # unless they are starting transmission
        if switch.upper() == 'START':
            if not self.tx_ready:
                self.tx_rx_setup()

        super(RRC, self).tx_rx_control(switch)

        return

    def tx_rx_setup(self):
        """Display a message box instructing the user how to set up RRC to pass traffic."""
        try:
            message_body = (
                'Packet transmission must be manually enabled on RRC!\n\nRun '
                'the following commands in EthAgent, replacing <slot_number> '
                'with an unused slot and <port_number> with the corresponding '
                'port (type LIST to show the mapping between <slot_number> - '
                'P(<port_number>)):\n\n1. ADD:<slot_number>\n2. HSS:'
                '<slot_number> MODE:10GBASE_SR\n3. SW TGPORT:<port_number> '
                '(<-- note this is port number!)'
            )

            ethspylib.message_box(
                ethspylib.MESSAGE_BOX_INFO,
                'Please setup packet transmission',
                message_body
            )

            # output  = self.dictify(self.port.execute("INFOLIST"))  # List all available ports
            # tg_port = output['SLOT']
            # self.port.execute("ADD %s" % tg_port)  # Add traffic generation port
            # self.port.execute("SW TGPORT:%s" % tg_port)  # Set it up as a traffic generation port
            # pause('ADD 35', 'ADD 35')
            # self.port.execute("ADD 35" % tg_port)  # Add traffic generation port
            # pause('Port 35 added', 'SW TGPORT:17')
            # self.port.execute("SW TGPORT:17" % tg_port)  # Set it up as a traffic generation port
            # pause('SW TGPORT:17')

            self.tx_ready = True  # Currently, it is assumed that the user set it up right
        except RuntimeError:
            print('TEST: RRC Tx setup failed!\n')

        return

    def coeff_file(self, coeffs, lane):
        """Write coefficients to a config file for Liberty Trail platform.
        
        The general format of the file is:
            api.platform.config.switch.0.portIndex.1.lane.2.preCursor10GCopper int 0
            api.platform.config.switch.0.portIndex.1.lane.2.cursor10GCopper int 0
            api.platform.config.switch.0.portIndex.1.lane.2.postCursor10GCopper int 0
        
        Args:
            coeffs (dict): A dictionary containing the coeffs, ordered by lane
            lane (int): The logical lane of the coefficients to write
        """
        print('\n\nWriting the Liberty Trail configuration file...\n')
        interface_list = []

        # Set variables dependent on the test being run
        if _ETHSPY_VARS['TEST_MODE'] == '100GBASE_SR4':
            interface_list = ['25GCopper', '25GOptical']
        elif _ETHSPY_VARS['TEST_MODE'] == 'XLPPI' or _ETHSPY_VARS['TEST_MODE'] == 'SFI10G':
            interface_list = ['10GCopper', '10GOptical']

        with open(r'%s/%s_Liberty_Trail_File.txt' % (
                _ETHSPY_VARS['OUTPUT_DIR'], _ETHSPY_VARS['DUT_NAME']
        ), 'a+') as lt_file:
            lt_file.write('\n')

            lt_file.write('\n#%s' % _ETHSPY_VARS['DUT_NAME'])
            lt_file.write('\n#Port %s' % device.slot)

            for lane, peaking in results_dict.items():
                lt_file.write('\n#Lane %s' % lane)
                for interface in interface_list:
                    for p_val, vals in peaking.items():
                        if vals['position'] == 0:
                            lt_file.write(
                                '\napi.platform.config.switch.0.portIndex.%s.lane.%s.preCursor%s int %s' % (
                                    self.slot_map[device.slot], lane, interface, vals['pre']
                                )
                            )
                            lt_file.write(
                                '\napi.platform.config.switch.0.portIndex.%s.lane.%s.cursor%s int %s' % (
                                    self.slot_map[device.slot], lane, interface, vals['main']
                                )
                            )
                            lt_file.write(
                                '\napi.platform.config.switch.0.portIndex.%s.lane.%s.postCursor%s int %s\n' % (
                                    self.slot_map[device.slot], lane, interface, vals['post']
                                )
                            )

    def decrease_amplitude(self, lane):
        """Calculate and apply a new main cursor value to decrease the amplitude.
        
        Red Rock Canyon's main tap is an attenuator, meaning that increasing 
        the C0 value decreases the amplitude. Before incrementing the main 
        tap, the value is checked to make sure it is not above 30. 
        This value is arbitrary and was determined from experience.
        
        Args:
            lane (int): The lane to decrease the amplitude on

        Returns:
            tuple: The new main cursor value, the limit flag
        """
        coeffs = self.get_coeffs(lane)

        if coeffs['C0'] < 30:
            new_c0 = coeffs['C0'] - self.tap
            self.hss(c0=new_c0)
            limit_flag = False
        else:
            new_c0 = coeffs['C0']
            limit_flag = True

        return new_c0, limit_flag

    def increase_amplitude(self, lane):
        """Calculate and apply a new main cursor value to increase the amplitude.

        Red Rock Canyon's main tap is an attenuator, meaning that decreasing 
        the C0 value increases the amplitude. Before decrementing the main 
        tap, the value is checked to make sure it is not below 0. 
        This value is arbitrary and was determined from experience.

        Args:
            lane (int): The lane to decrease the amplitude on

        Returns:
            tuple: The new main cursor value, the limit flag
        """
        coeffs = self.get_coeffs(lane)

        if coeffs['C0'] != 0:
            new_c0 = coeffs['C0'] + self.tap
            self.hss(c0=new_c0)
            limit_flag = False
        else:
            new_c0 = coeffs['C0']
            limit_flag = True

        return new_c0, limit_flag

    def slot_to_port_mapping(self):
        """Map the EthAgent slot numbers to logical port numbers and return them.
        
        Returns:
            dict: Slot to port mapping.
        """
        d = {}

        list_output = self.port.execute('hostCommand LIST')
        list_output = list_output.split('\r\n')

        for l in list_output:
            try:
                lsplit = l.split('-')
                slot = lsplit[0].strip()
                right = lsplit[1].strip()
                right = right.lstrip('P(')
                right_split = right.split(')')
                port = right_split[0]
                d[int(slot)] = int(port)
            except (ValueError, IndexError):
                pass

        return d

    @staticmethod
    def ethspy_module_info_get_all():
        return {'VENDOR NAME': 'Unspecified', 'VENDOR PN': 'Unspecified'}

