"""This module provides functions to help in running EthTests."""
# Standard library imports
import errno
import os
import shutil

# Local project imports.
import ethspylib


def create_data_directory(vars_dict, ln, coeffs=None):
    if not coeffs:
        coeffs = {}

    if vars_dict['test_suite'] == 'SFI':
        base_folder = vars_dict['OUTPUT_DIR']
        suite_folder = os.path.join(
            base_folder,
            '{}_port{}_slot{}_{}_{}_{}_{}'.format(
                vars_dict['identifier'],
                vars_dict['device'].ethspy_summary_get_status()['FUNCTION'],
                vars_dict['device'].slot,
                vars_dict['coeff_type'],
                coeffs[ln]['CM1'],
                coeffs[ln]['C0'],
                coeffs[ln]['C1']
            )
        )
    else:
        base_folder = os.path.join(
            vars_dict['OUTPUT_DIR'],
            '{}_port{}_slot{}'.format(
                vars_dict['identifier'],
                vars_dict['device'].ethspy_summary_get_status()['FUNCTION'],
                vars_dict['device'].slot
            )
        )
        suite_folder = os.path.join(
            base_folder,
            '_'.join(
                [
                    vars_dict['test_suite'],
                    vars_dict['coeff_type']
                ]
            )
        )

    lane_folder = os.path.join(suite_folder, 'lane{}'.format(ln))
    data_folder = os.path.join(lane_folder, 'data')

    create_folder(data_folder)

    return base_folder, suite_folder, lane_folder, data_folder


def create_folder(folder):
    if not os.path.exists(folder):
        try:
            os.makedirs(folder)
        except OSError as exc:  # Guard against a race condition
            if exc.errno != errno.EEXIST:
                raise ethspylib.EthSpyError(
                    'Error creating data directory! Ending script!'
                )


def create_tuning_directory(vars_dict):
    tuning_folder = os.path.join(vars_dict['lane_folder'], 'tuning')

    create_folder(tuning_folder)

    return tuning_folder


def delete_data_directory(vars_dict):
    """Delete the directory containing the scope waveform files.

    vars_dict['data_folder'] is set to None if the folder is deleted.

    :param dict vars_dict: The test variables
    """
    if vars_dict['cleanup'] == 'Enable':
        shutil.rmtree(vars_dict['data_folder'], ignore_errors=True)
        vars_dict['data_folder'] = None


def extend_list_length(long_list, short_list):
    """Makes the short list to be the same length as the long list.

    The new list is created by copy duplicates of the short list until the length of
    the long list has been reached.

    Args:
        long_list (list): The desired length of the new list.
        short_list (list): The list to be lengthened.

    Returns:
        list: A list that is the same length as the long list.
    """
    new_list = short_list
    if len(long_list) > len(short_list):
        diff = len(long_list) - len(short_list)
        val = (diff // len(short_list)) + 1

        if len(long_list) % len(short_list) == 0:
            val -= 1

        for _ in range(0, val):
            new_list.extend(short_list)

    return new_list


def get_hostname_and_slot(prt):
    """Gets the hostname and slot number from the port then closes it.

    Args:
        p (obj): The port to retrieve hostname and slot from.

    Return:
        tuple: Hostname and slot
    """
    try:
        hst_nm = prt.host_name
        slt_num = int(prt.slot_number)
        prt.close()
    except KeyError:
        raise ethspylib.EthSpyError(
            'Error determining hostname or slot number! Ending script...'
        )

    return hst_nm, slt_num


def get_shared_drive_letter():
    """Gets the drive letter of the shared drive.

    Returns:
        str: The drive letter of the shared drive
    """
    try:
        drive_letter = os.path.splitdrive(_ETHSPY_VARS['OUTPUT_DIR'])[0]
        # __builtin__._ETHSPY_VARS['SHARED_DRIVE_LETTER'] = drive_letter
    except KeyError:
        raise ethspylib.EthSpyError(
            'Error determining output directory drive letter! '
            'UNC paths are not supported! Ending script...'
        )

    return drive_letter


def hcb_message(slt, number_hcbs):
    """Displays a message telling the user to change which ports the HCB is plugged into.

    Args:
        slt (): The slot that is being tested.
        number_hcbs (int): The number of HCBs being used for the test.
    """
    if _ETHSPY_VARS['manual'] == 'AUTOMATIC':
        if number_hcbs == 4:
            message = (
                "User Intervention Required:\nPlease connect the HCB's to "
                "the next 4 sequential\nslots starting with slot {} and then "
                "click OK.".format(slt)
            )
            ethspylib.message_box(
                ethspylib.MESSAGE_BOX_INFO, 'Test Paused', message
            )
        else:
            message = (
                'User Intervention Required:\nPlease connect the HCB to slot '
                '{} and then click OK.'.format(slt)
            )
            # d.blink()
            ethspylib.message_box(
                ethspylib.MESSAGE_BOX_INFO, 'Test Paused', message
            )
    else:
        message = (
            'User Intervention Required:\nPlease connect the HCB to the slot '
            'under test and then click OK.'
        )
        ethspylib.message_box(
            ethspylib.MESSAGE_BOX_INFO, 'Test Paused', message
        )


def json_file():
    filename = os.path.join(
        _ETHSPY_VARS['OUTPUT_DIR'],
        '_'.join([id_string, 'slot%s' % dut_slot, dut.summary['FUNCTION']]),
        test_type,
        '%s_results.json' % test_type
    )
    with open(filename, 'w') as fh:
        json.dump(
            test.data, fh, sort_keys=True, indent=4, separators=(',', ': ')
        )


def process_lane_list(selected_lanes, suite):
    """

    :param str selected_lanes:
    :param str suite:
    :return:
    """
    print('suite = ', suite)
    print('selected_lanes = ', selected_lanes)
    lane_dict = {
        '10GBASE-T': [0, 1, 2, 3],
        '25GBASE-CR': [0],
        '40GBASE-CR4': [0, 1, 2, 3],
        'AUI': [0],
        'SFI': [0],
        'XLPPI': [0, 1, 2, 3],
        '10G HSS': [0],
        '25G HSS': [0],
        '100G HSS': [0, 1, 2, 3],
        '10GReturnLoss': [0],
        '25GReturnLoss': [0],
        '40GReturnLoss': [0, 1, 2, 3],
        '100GReturnLoss': [0, 1, 2, 3]
    }

    try:
        if selected_lanes.upper() == 'ALL':
            lane_lst = lane_dict[suite]
        else:
            lane_lst = []
            for num in selected_lanes.split(';'):
                num = int(num)
                if lane_dict[suite][0] <= num <= lane_dict[suite][-1]:
                    lane_lst.append(int(num))
                else:
                    raise ethspylib.EthSpyError(
                        'Lane selection out of range! Lanes must be'
                        ' between {} and {}. Ending script...'.format(
                            lane_dict[suite][0], lane_dict[suite][-1]
                        )
                    )
    except KeyError:
        raise ethspylib.EthSpyError(
            'Error processing lane choices! Ending script...'
        )

    return lane_lst


def process_shorthand_list(s_list):
    """Process the slot list shorthand into a true Python list.

    Valid shorthand expressions:
        "x-y": Fill in the numbers between x and y.
        "x;y": Take x and y only, don't fill in the numbers between them.

    Args:
        s_list (list): A list of slots that can contain the shorthand expressions above.

    Returns:
        list: An explicit list of slots

    Raises:
        ethspylib.EthSpyError: If a key is not found.
    """
    try:
        slot_list = []
        temp_sl = s_list.split(';')
        for s in temp_sl:
            if '-' in s:
                s_split = s.split('-')
                for num in range(int(s_split[0]), int(s_split[1])+1):
                    slot_list.append(int(num))
            else:
                slot_list.append(int(s))
    except KeyError:
        raise ethspylib.EthSpyError(
            'Error processing the slot list! Ending script...'
        )

    return slot_list


def process_suite_list(suite):
    # output = []
    translate = {
        '10G HSS': ['SFI'],
        '25G HSS': ['25GBASE-CR', 'AUI'],
        '40G HSS': ['XLPPI'],
        '100G HSS': ['25GBASE-CR', 'AUI'],
        '10GBASE-T': ['10GBASE-T'],
        '10/100/1000 BASE-T': [],
        '10GReturnLoss': ['10GReturnLoss'],
        '25GReturnLoss': ['25GReturnLoss'],
        '40GReturnLoss': ['40GReturnLoss'],
        '100GReturnLoss': ['100GReturnLoss']
    }
    # temp = suite.split()
    # '25G HSS': ['25GBASE-CR', 'AUI'],

    output = translate[suite]
    # try:
    #     speeds = temp[0].split('/')
    #     for speed in speeds:
    #         output.append(''.join([speed, temp[1]]))
    # except IndexError:
    #     output = temp

    return output


def process_test_list(selected_test):
    """Process the test list to figure out which tests to run.

    :param selected_test:
    :return: The processed test list
    :rtype: list
    """
    test_to_suite_map = {
        'OutputWaveform': '25GBASE-CR',
        'EffectiveJitter': '25GBASE-CR',
        'PeakingTest': 'AUI',
        'RiseTimeFallTime': 'AUI',
        'AcCommon': 'SFI',
        'DDJ': 'SFI',
        'DDPWS (SFI)': 'SFI',
        'Eye': 'SFI',
        'QSQ': 'SFI',
        'RFT': 'SFI',
        'TJ': 'SFI',
        'TWDPc': 'SFI',
        'UJ': 'SFI',
        'VMA': 'SFI',
        'Common Mode': 'XLPPI',
        'DDPWS (XLPPI)': 'XLPPI',
        'Eye Mask': 'XLPPI',
        'J2 Jitter': 'XLPPI',
        'J9 Jitter': 'XLPPI',
        'Rise Time - Fall Time': 'XLPPI',
        'Qsq': 'XLPPI'
    }
    try:
        # Figure out which tests to run...
        suite = [test_to_suite_map['selected_test']]
        test_lst = [selected_test]
    except KeyError:
        raise ethspylib.EthSpyError(
            'Error determining which tests to run! Ending script...'
        )

    return suite, test_lst


def process_slot_ip_port_list(raw_list):
    list_of_lists = []
    split_list = raw_list.split(';')
    for seq in split_list:
        list_of_lists.append(seq.split(':'))

    return list_of_lists


def scope_init(scope_conn):
    from equipment.scopes import generic_scope as scope

    scope_obj = scope.GenericScope(scope_conn)

    if '86100D' in scope_obj.idn['Model']:
        from equipment.scopes import keysight_86100d as samp_scope
        scope_obj = samp_scope.Keysight86100D(scope_conn)
        print('Scope identified as a Keysight 86100D.')
    elif scope_obj.idn['Model'] in ['DSOX91604A', 'DSOX92004A']:
        from equipment.scopes import keysight_dsox91604a as dsox
        scope_obj = dsox.KeysightDSOX91604A(scope_conn)
        print('Scope identified as a Keysight {}.'.format(scope_obj.idn['Model']))
    elif 'DSA70804C' in scope_obj.idn['Model']:
        from equipment.scopes import tek_dsa70804c as tek
        scope_obj = tek.tek_dsa70804c.TekDSA70804C(scope_conn)
        print('Scope identified as a Tektronix DSA70804C.')

    return scope_obj


def switch_init(switch_conn):
    from equipment.switches import generic_switch as switch

    sw = switch.GenericSwitch(switch_conn)

    if 'JFW' in sw.idn:
        from equipment.switches import jfw_50sa_288
        sw = jfw_50sa_288.JFW50SA288(switch_conn)
        print('Switch identified as a JFW 50SA-288.')
    elif 'MODEL SYSTEM 46' in sw.idn:
        from equipment.switches import keithley_s46t
        sw = keithley_s46t.KeithleyS46T(switch_conn)
        print('Switch identified as a Keithley S46T.')
    elif 'PXI' in sw.idn:
        from equipment.switches import pxi
        sw = equipment.switch.pxi.PXI(switch_conn)
        print('Switch identified as a PXI.')

    return sw


def round2(num, digits):

    """
    Round to nearest
    Tie goes away from zero

    After 100,000,000 trials comparing this function to Python 2's
    built in round function when rounding to 6 decimal places, 5
    errors were observed. The maximum difference between return
    values was 1.00000000032e-05

    After 100,000,000 trials comparing this function to Python 2's
    built in round function when rounding to 12 decimal places,
    35422 errors were observed (0.035%). The maximum difference
    between return values was 9.99999940632e-08
    """

    from math import floor, ceil

    p = 10 ** digits

    if num > 0:
        return float(floor((num * p) + 0.5))/p
        
    else:
        return float(ceil((num * p) -0.5))/p
