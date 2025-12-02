from __future__ import print_function
from __future__ import absolute_import
import ethspylib


class ManualOverride(object):
    """This class is used for manual conformance testing.

    .. note: This class inherits from "object" and not "DUT".

    This class should always return a generic value (string = "N\A", 
        number = 999) for any method called or pass if the method doesn't 
        need to be run. All of the variables set in the 
        :meth:`ManualOverride.__init__` method should also return "N\A" or 
        999. Some methods may get info from the calling XML file.
    """

    def __init__(self, port):
        self.branding_string = 'N/A'
        self.codename = 'ManualOverride'
        self.pcie = 'N/A'
        self.pcie_bdf = '999:999.999'
        self.port = port
        self.device_id = 'N/A'
        self.slot = self.port.slot_number
        self.slot_number = self.port.slot_number

        self.mac_addr = '999999999999'

        self.ea_version = 'N/A'
        self.qv_version = 'N/A'

        self.phy_port = 'N/A'

        self.tap_settings = [
            [999, 999, 999, 'tap0'],
            [999, 999, 999, 'tap1'],
            [999, 999, 999, 'tap2'],
            [999, 999, 999, 'tap3'],
            [999, 999, 999, 'tap4'],
            [999, 999, 999, 'tap5'],
            [999, 999, 999, 'tap6'],
            [999, 999, 999, 'tap7'],
            [999, 999, 999, 'tap8'],
            [999, 999, 999, 'tap9']
        ]

        self.caui_coeffs = [[999, 999, 999]]

    @staticmethod
    def adminq_control(state):
        print('MANUAL OVERRIDE MODE: If testing a Fortville, set ADMINQ to %s' % state)
        return

    @staticmethod
    def clear_counters():
        print('MANUAL OVERRIDE MODE: Not possible to clear QR counters')
        pass

    def close(self):
        pass

    def coeff_file(self, coeffs, lane):
        pass

    @staticmethod
    def decrease_amplitude(lane):
        """Display a message to the operator to decrease the amplitude.

        :param int lane: The lane number under to decrease
        """
        print('MANUAL OVERRIDE MODE: Amplitude decrease required')

        ethspylib.message_box(
            ethspylib.MESSAGE_BOX_INFO,
            'MANUAL OVERRIDE MODE',
            'Decrease the amplitude on the DUT by 1' % switch
        )

        return

    def dict_to_list(self, lst, d):
        output_list = []

        for self.val in lst:
            output_list.append(d[self.val])

        return output_list

    def ethspy_summary_get_status(self):
        """Run the ETHSPY SUMMARY GET-STATUS command, convert it to a Python dictionary, and return it.

        :return: Output of the command
        :rtype: dict
        """
        output = {
            "BAR0": "0",
            "BAR1": "0",
            "BAR2": "0",
            "BAR3": "0",
            "BAR4": "0",
            "BAR5": "0",
            "BUS": "0",
            "DEBUG-MODE": "Enabled",
            "DEVICE": "0",
            "DEVICE-ID": "9999",
            "DEVICE-NAME": "Intel(R) Ethernet Network Adapter XXV999",
            "ETRACK-ID": "0x9999999",
            "EXPANSION-BAR": "0",
            "EXTERNAL-PHY-TYPE": "BASE",
            "FIRMWARE-REVISION": "FW:9.99 API:9.9 DBG",
            "FUNCTION": "0",
            "LANES-COMPANION-PHY-HOST": 0,
            "LANES-COMPANION-PHY-LINE": 1,
            "LANES-PRIMARY-PHY-HOST": 0,
            "LANES-PRIMARY-PHY-LINE": 4,
            "MAC-ADDRESS": "ABCDEFABCDEF",
            "NVM-REVISION": "9.99 MAP9.99",
            "REVISION-ID": "0",
            "SERDES-TEMPERATURE": "99999 mC",
            "SUBSYSTEM-ID": "0",
            "SUBVENDOR-ID": "9999",
            "VENDOR-ID": "9999"
        }

        return output

    @staticmethod
    def get_branding_string(raw=-1):
        print('MANUAL OVERRIDE MODE: Not possible to get branding string')
        return 'N\A'

    @staticmethod
    def get_codename(raw=-1):
        print('MANUAL OVERRIDE MODE: Not possible to get codename')
        return 'N\A'

    @staticmethod
    def get_coeffs(lane=-1):
        """Return placeholder values for the coefficients.

        :param int lane: The lane requested
        :return: Dummy values
        :rtype: dict
        """
        print('MANUAL OVERRIDE MODE: Not possible to get coeffs')
        if lane == -1:
            if _ETHSPY_VARS['CURRENT_TEST'] in ['SFI', '25GBASE-CR', 'CAUI']:
                output_dict = {0: {'LANE': lane, 'CM1': 999, 'C0': 999, 'C1': 999}}
            elif _ETHSPY_VARS['CURRENT_TEST'] in ['40GBASE-CR4', 'XLPPI', '100GBASE-CR4',
                                                  'CAUI-4']:
                output_dict = {0: {'LANE': lane, 'CM1': 999, 'C0': 999, 'C1': 999},
                               1: {'LANE': lane, 'CM1': 999, 'C0': 999, 'C1': 999},
                               2: {'LANE': lane, 'CM1': 999, 'C0': 999, 'C1': 999},
                               3: {'LANE': lane, 'CM1': 999, 'C0': 999, 'C1': 999}}
        else:
            output_dict = {lane: {'LANE': lane, 'CM1': 999, 'C0': 999, 'C1': 999}}

        return output_dict

    @staticmethod
    def get_device_id(ea_input=-1):
        print('MANUAL OVERRIDE MODE: Not possible to get device ID')
        return 'N\A'

    @staticmethod
    def get_ea_version(ea_input=-1):
        print('MANUAL OVERRIDE MODE: EthAgent version')
        return 'N\A'

    @staticmethod
    def get_hostname():
        print('MANUAL OVERRIDE MODE: Not possible to get HOSTNAME')
        return 'N\A'

    @staticmethod
    def get_initial_coeffs(lane):
        r = {
            0: {'CM1': 0, 'C0': 0, 'C1': 0},
            1: {'CM1': 0, 'C0': 0, 'C1': 0},
            2: {'CM1': 0, 'C0': 0, 'C1': 0},
            3: {'CM1': 0, 'C0': 0, 'C1': 0}
        }

        return r

    @staticmethod
    def get_link_mode(ea_input=-1):
        print('MANUAL OVERRIDE MODE: Not possible to get the link mode')
        return 'N\A'

    @staticmethod
    def get_link_status(ea_input=-1):
        print('MANUAL OVERRIDE MODE: Not possible to get link status')
        return 'N\A'

    @staticmethod
    def get_mac_addr(ea_input=-1):
        print('MANUAL OVERRIDE MODE: Not possible to get MAC address')
        return '000000000000'

    @staticmethod
    def get_module_info():
        print('MANUAL OVERRIDE MODE: Not possible to get module info')
        return {'module_vendor': 'N\A', 'module_part_number': 'N\A',
                'module_compliance_code': 'N\A'}

    def get_pcie(self, ea_input=-1):
        print('MANUAL OVERRIDE MODE: Not possible to get PCIE BDF')
        self.pcie = {'BUS': 999, 'DEVICE': 999, 'FUNCTION': 999}
        return self.pcie

    @staticmethod
    def get_qr_counter():
        print('MANUAL OVERRIDE MODE: Not possible to read QR counter')
        pass

    @staticmethod
    def get_qv_version(ea_input=-1):
        print('MANUAL OVERRIDE MODE: Not possible to get QV version')
        return 'N\A'

    @staticmethod
    def get_rxdfe(lane=-1):
        print('MANUAL OVERRIDE MODE: Not possible to get RXDFE')
        return 'N\A'

    @staticmethod
    def get_rxffe(lane=-1):
        print('MANUAL OVERRIDE MODE: Not possible to get RXFFE')
        return 'N\A'

    @staticmethod
    def get_rx_status():
        print('MANUAL OVERRIDE MODE: Not possible to run GETRXSTATUS')
        return 'N\A'

    @staticmethod
    def get_rxtdfe(lane=-1):
        print('MANUAL OVERRIDE MODE: Not possible to get RXTDFE')
        return 'N\A'

    @staticmethod
    def get_slot(ea_input=-1):
        print('MANUAL OVERRIDE MODE: Not possible to get slot')
        return 999

    @staticmethod
    def get_snr(lane=-1):
        print('MANUAL OVERRIDE MODE: Not possible to get VOM/SNR/EHM')
        return 999

    @staticmethod
    def get_speed(ea_input=-1):
        print('MANUAL OVERRIDE MODE: Not possible to get SPEED')
        return '999G'

    @staticmethod
    def get_ttl():
        print('MANUAL OVERRIDE MODE: Not possible to get TTL')
        return 999

    @staticmethod
    def get_txffe(lane=-1):
        print('MANUAL OVERRIDE MODE: Not possible to get TXFFE')
        return 999

    @staticmethod
    def get_vga(lane=-1):
        print('MANUAL OVERRIDE MODE: Not possible to get VGA')
        return 999

    @staticmethod
    def hss(mode=-1, pattern=-1, lane=-1, cm1=-1, c0=-1, c1=-1):
        names = ['LANE', 'MODE', 'PATTERN']
        vals = [lane, mode, pattern]

        # Build up the message box body
        box_body = 'Set the DUT to the following:'
        for name, val in zip(names, vals):
            if val != -1:
                box_body += "\n\t%s: %s" % (name, val)
            else:
                pass
        box_body += '\n\tCoeffs: As appropriate for the test.'
        box_body += '\nTo continue, click OK.'

        print(box_body)

        # Display the message box
        print('MANUAL OVERRIDE MODE: Coefficient/mode/pattern control required')
        ethspylib.message_box(
            ethspylib.MESSAGE_BOX_INFO,
            'MANUAL OVERRIDE MODE',
            box_body
        )

        return vals

    @staticmethod
    def increase_amplitude(lane):
        """Display a message to the operator to increase the amplitude.

        :param int lane: The lane number under to increase
        """
        print('MANUAL OVERRIDE MODE: Amplitude increase required')

        ethspylib.message_box(
            ethspylib.MESSAGE_BOX_INFO,
            'MANUAL OVERRIDE MODE',
            'Increase the amplitude on the DUT by 1'
        )
        return

    @staticmethod
    def infolist():
        print('MANUAL OVERRIDE MODE: No EthAgent INFOLIST')

        infolist_stub = '''SLOT: 999

        BRANDING_STRING: N/A

        CODENAME: N/A

        ADAPTER_CODENAME: N/A

        VENDOR_ID: N/A

        DEVICE_ID: N/A

        REVISION_ID: N/A

        SUBSYSTEM_ID: N/A

        SUBSYSTEM_VENDOR_ID: N/A

        BUS: 999

        DEVICE: 999

        FUNCTION: 999

        INITIALIZED: N/A

        INIT_TYPE: N/A

        PCI_CLASS: N/A

        PCI_SUBCLASS: N/A

        CONNECTION_CLASS: N/A

        ETRACK_ID: N/A

        MEDIA_TYPE: N/A

        PHY_TYPE: N/A

        PHY_ID: N/A

        '''

        return infolist_stub

    @staticmethod
    def show():
        print('MANUAL OVERRIDE MODE: No EthAgent SHOW')
        return 'N\A'

    @staticmethod
    def status():
        print('MANUAL OVERRIDE MODE: No EthAgent STATUS')
        return 'N\A'

    @staticmethod
    def summary_get_status():
        return {'STATUS': 'N/A'}

    @staticmethod
    def tx_rx_control(switch):
        """Display a message to the operator to start or stop packet transmission on the DUT.

        :param str switch: "START" or "STOP"
        """
        print('MANUAL OVERRIDE MODE: Tx/Rx control required')

        ethspylib.message_box(
            ethspylib.MESSAGE_BOX_INFO,
            'MANUAL OVERRIDE MODE',
            'Tx/Rx Control: %s Tx/Rx' % switch
        )

        return

    def update_vars(self):
        print('MANUAL OVERRIDE MODE: Variables not updated')
        return {
            'branding_string': self.branding_string,
            'codename': self.codename,
            'pcie': self.pcie,
            'mac_addr': self.mac_addr,
            'link_mode': self.link_mode,
            'speed': self.speed,
            'slot': self.slot
        }

    @staticmethod
    def version():
        print('MANUAL OVERRIDE MODE: No EthAgent VERSION')

        version_stub = '''NPPV Remote Version N/A

        QV Version N/A

        Switch API: N/A

        INTERNAL USE ONLY
        '''

        return version_stub
