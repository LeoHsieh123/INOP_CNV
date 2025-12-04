"""
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
"""
# print('Waiting for Debugger To Connect (5 Minute Timeout)... \n\n')
# import rpdb2
# rpdb2.start_embedded_debugger('314159')

# Standard library imports
from collections import Counter
import setuptools, sys
sys.modules['distutils'] = setuptools._distutils
#from distutils import file_util
from distutils import file_util
#from distutils.errors import DistutilsFileError
from distutils.errors import DistutilsFileError
import csv
import errno
import json
import math
import os
import subprocess
import time

# Local project imports
from common.helpers import round2
import ethspylib

es_vars = _ETHSPY_VARS  # _ETHSPY_VARS is created by Ethernet Inspector and passed into the script

class LHC:
    """This class provides the core functionality for the LHC test.

    Attributes:

    """
    def __init__(self, dut, lp, link_attempts, ber_iterations, channel,
                 dut_name, lp_name, ttl_delay, retry_ttl, logger):
        """

        Args:
            dut (obj): Object to control the DUT device.
            lp (obj): Object to control the link partner device.
            link_attempts (int):
            ber_iterations (int):
            channel (str):
            dut_name (str):
            lp_name (str):
            ttl_delay (int):
            retry_ttl (int):
        """
        self.start = time.time()
        self.test_complete = False
        self.output_dir = es_vars['OUTPUT_DIR']
        self.reset_side = es_vars['RESET_SIDE']
        self.ber_target = es_vars['BER_TARGET']
        self.collect_hostinfo = es_vars['COLLECT_HOSTINFO']
        self.winpy, self.winpy_folder, self.winpy_exe_folder = self.find_winpython()

        # Initialize a few variables
        self.ber_counter, self.dut_gprc, self.dut_ber_confidence = 0, 0, 0
        self.dut = dut
        self.link_partner = lp
        self.ber_iterations = ber_iterations
        if link_attempts == 0:
            self.link_attempts = ber_iterations
            self.bypass_ttl = 1
        else: 
            self.link_attempts = link_attempts
            self.bypass_ttl = 0
        self.ttl_delay = ttl_delay
        self.logger = logger
        # 1 mandatory attempt + user defined retry attempts.
        self.retry_ttl = retry_ttl + 1

        # Need to make sure link is up or else the test is pointless
        self.check_link(self.dut.ethspy_link_get_status()['LINK-UP'])

        # Add class level attributes for the name of the DUT and LP
        self.dut.name = dut_name
        self.link_partner.name = lp_name

        # Add class level attributes identifying the DUT and LP as such
        self.dut.id = 'DUT'
        self.link_partner.id = 'LP'

        # Add class level attributes to the DUT and LP for SNR control
        self.dut.snr_control = es_vars['DUT_SNR_CONTROL']
        self.link_partner.snr_control = es_vars['LP_SNR_CONTROL']

        # Add class level attribute to the DUT and LP to enable testing
        self.dut.test_enabled = 'Enable'
        self.link_partner.test_enabled = es_vars['LP_DATA']

        self.castes_vars()
        self.set_packet_size()
        self.check_confidence_level()
        self.channel = channel

        self.disable_ehm_dnv()

        # Create the data container and add the static information to it
        self.data = {'TestName': 'LHC'}

        if self.channel.lower() == 'auto':
            self.module_info = self.dut.ethspy_module_info_get_all()
            self.data = self.store_static_data(
                self.module_info, self.data, ('MODULE-INFO',)
            )
        else:
            self.module_info = self.channel

        self.static_device_info(self.dut)
        self.static_device_info(self.link_partner)

        if es_vars['DUT_EEPROM_DUMP'] == 'Enable':
            self.save_eeprom(self.dut)

        if es_vars['LP_EEPROM_DUMP'] == 'Enable' and es_vars['LP_DATA'] == 'Enable':
            self.save_eeprom(self.link_partner)

        self.check_max_filename_length()

    def main_test(self):
        """Runs the LHC test and controls the main loop.

        Only the TTL, EHM, and BER tests are allowed run if the device is Lewisberg.
        """
        for iteration in range(1, self.link_attempts + 1):
            self.iteration_info(iteration)
            if self.bypass_ttl == 0:
                self.run_ttl()

            time.sleep(10)
            for device in [self.dut, self.link_partner]:
                if device.test_enabled == 'Enable':

                    if device.codename != 'Lewisberg':
                        self.run_link_get_status(device)

                    for lane in range(0, 4):
                        if device.codename != 'Lewisberg':
                            self.run_training_coeff_log(device, lane, iteration)

                        self.run_snr(device, lane, iteration)

                        if device.codename != 'Lewisberg':
                            self.run_rx_get_status(device, lane)
                            self.run_tx_get_status(device, lane)
                            self.run_lane_get_status(device, lane)
                            self.run_rx_get_ehm(device, lane)  # Snowridge only!

                    #self.logger.info('\n')
                    
            ber_data = self.ber_run(iteration)
            for k in ber_data:
                self.store_data(ber_data[k], self.data, (k, 'BER'))

        self.data = self.statistics(self.data)
        self.test_complete = True

        return self.data

    def add_static_data(self, data, dictionary):
        """Adds static data to the data dictionary.

        Static data needs to be handled differently from dynamic data.

        Note: This is a recursive method!

        Args:
            data (dict): The data to add.
            dictionary (dict): The dictionary to store the data into.
        """
        for key in data:
            if isinstance(data[key], dict):
                try:
                    dictionary[key].update(
                        self.add_static_data(data[key], dictionary[key])
                    )
                except KeyError:
                    # this is where a new key gets added
                    dictionary[key] = {}
                    dictionary[key].update(
                        self.add_static_data(data[key], dictionary[key])
                    )
            else:
                dictionary[key] = data[key]

        return dictionary

    def append_data(self, data, dictionary):
        for key in data:
            if isinstance(data[key], dict):
                try:
                    dictionary[key].update(
                        self.append_data(data[key], dictionary[key])
                    )
                except KeyError:
                    dictionary[key] = {}
                    dictionary[key].update(
                        self.append_data(data[key], dictionary[key])
                    )
            else:
                if isinstance(data[key], list):
                    try:
                        dictionary[key].extend(data[key])
                    except (KeyError, AttributeError, TypeError):
                        dictionary[key] = data[key]
                else:
                    try:
                        dictionary[key].append(data[key])
                    except (KeyError, AttributeError, TypeError):
                        dictionary[key] = []
                        dictionary[key].append(data[key])

        return dictionary

    def backfill_ber_data(self, ber_data, i, side):
        if 'BER' not in self.data[side] or not self.data[side]['BER']:
            for key in ber_data:
                ber_data[key] = [ber_data[key]]
                for _ in range(1, i):
                    ber_data[key].insert(0, 'N/A')

        return ber_data

    def ber_run(self, iteration):
        self.ber_snr_check()
        time.sleep(5)
        
        if self.ber_iterations > 0:
            ber_info = self.ber_test(iteration)
            for k in ber_info:
                self.backfill_ber_data(ber_info[k], iteration, k)

            self.ber_iterations -= 1   # Keep BER from continuing to run
        else:
            ber_info = {}
            for side in [self.dut, self.link_partner]:
                if side.test_enabled == 'Enable':
                    if 'BER' in self.data[side.id]:
                        for k in self.data[side.id]['BER']:
                            try:
                                ber_info[side.id].update({k: 'N/A'})
                            except KeyError:
                                ber_info[side.id] = {k: 'N/A'}

        return ber_info

    def ber_snr_check(self):
        for lane in range(0, self.dut.lanes):
            stored_ber_iterations = self.ber_iterations

            for snr_string in self.dut.snr_type:
                try:
                    lst = self.data['DUT']['SNR'][lane][snr_string]
                    if lst[-1] < es_vars['BER_THRESHOLD'] \
                            and self.ber_iterations == 0:
                        # Increment ber_iterations to force it to run
                        self.ber_iterations += 1
                        break
                except (IndexError, KeyError, TypeError):
                    pass

            if stored_ber_iterations != self.ber_iterations:
                break

    def ber_test(self, iteration):
        # dut_ber_confidence, dut_errors, bits_received, dut_gprc = 0, 0, 0, 0

        self.logger.info('-------------------------------------------')
        self.logger.info('Running BER measurement')
        self.logger.info('-------------------------------------------')

        drop_errors = 0
        symbol_error = False
        symbol_error_lp = False

        # Start transmit and receive
        self.dut.clear_counters()
        self.link_partner.clear_counters()
        time.sleep(1)
        self.dut.tx_rx_control('START')
        time.sleep(1)
        self.link_partner.tx_rx_control('START')
        time.sleep(1)



        t_initial = time.time()
        while True:
            # Get the packets received and errors etc.
            stats = self.dut.ethspy_link_get_stats()
            dut_errors, symbol_error = self.sum_rcv_errors(stats, symbol_error)
            
            stats_lp = self.link_partner.ethspy_link_get_stats()
            lp_errors, symbol_error_lp = self.sum_rcv_errors(stats_lp, symbol_error_lp)

            # Run a QR to get the current RX packet count...
            # dut_gprc, dut_errors = self.dut.get_qr_counter()

            bits_received = (
                stats['QR-GOOD-RECEIVES']
                * es_vars['BER_PACKET_SIZE']
                * 8
            )
            
            bits_received_lp = (
                stats_lp['QR-GOOD-RECEIVES']
                * es_vars['BER_PACKET_SIZE']
                * 8
            )

            # Compute the confidence level
            dut_ber_confidence = self.ber_compute_confidence_level(
                dut_errors+drop_errors, bits_received
            )

            t_secondary = time.time()
            t_delta = t_secondary - t_initial

            # Get the bit rate
            bit_rate_gbps = self.dut.bandwidth()['RX-MBPS'] / 1000.0
            bit_tx_rate_gbps = self.dut.bandwidth()['TX-MBPS'] / 1000.0
			
            lp_bit_rate_gbps = self.link_partner.bandwidth()['RX-MBPS'] / 1000.0
            lp_bit_tx_rate_gbps = self.link_partner.bandwidth()['TX-MBPS'] / 1000.0

            self.display_ber(
                t_delta, iteration, bit_rate_gbps, bit_tx_rate_gbps, lp_bit_rate_gbps, lp_bit_tx_rate_gbps, stats['QR-GOOD-RECEIVES'],
                dut_errors+drop_errors, dut_ber_confidence
            )

            if t_delta > es_vars['BER_TIMEOUT']:
                self.logger.info(
                    'The {} second timeout for the BER test has been reached!'.format(
                        es_vars['BER_TIMEOUT']
                    )
                )
                self.logger.info('Ending BER test now!')
                self.link_partner.tx_rx_control('STOP')
                time.sleep(10)
                self.dut.tx_rx_control('STOP')
                time.sleep(10)
                break

            if dut_errors+drop_errors > es_vars['BER_ERROR_THRESHOLD']:
                self.logger.info(
                    'Error threshold of {} has been exceeded!'.format(
                        es_vars['BER_ERROR_THRESHOLD']
                    )
                )
                self.logger.info('Ending BER test now!')
                self.link_partner.tx_rx_control('STOP')
                time.sleep(10)
                self.dut.tx_rx_control('STOP')
                time.sleep(10)
                break

            if dut_ber_confidence >= es_vars['BER_CONFIDENCE']: 
                if (self.link_partner.test_enabled == 'Enable'
                        and es_vars['DROPPED_PACKETS'] == 'Enable'):
                    drop_errors, delta = self.dropped_packet_check(drop_errors)
                    '''if delta == 0:'''
                    break
                else:
                    break

            time.sleep(1)  # Poll the number of packets once a second

        # Stop transmit and receive
        #self.dut.tx_rx_control('STOP')
        #self.link_partner.tx_rx_control('STOP')

        try:
            dut_measured_ber = float(dut_errors) / float(bits_received)
            lp_measured_ber = float(lp_errors) / float(bits_received_lp)
            self.logger.info('DUT error is {}'.format(dut_errors))
            self.logger.info('Measured DUT BER is {:.29f}\n'.format(dut_measured_ber))
            
            self.logger.info('LP error is {}'.format(lp_errors))
            self.logger.info('Measured LP BER is {:.29f}\n'.format(lp_measured_ber))
            
        except ZeroDivisionError:
            dut_measured_ber = 'Error'

        ber_pf = self.ber_pass_fail(dut_ber_confidence)

        return_data = {
            'DUT': {
                'CONFIDENCE': dut_ber_confidence,
                'ERRORS': dut_errors,
                'GPRC': stats['QR-GOOD-RECEIVES'],
                'MEASURED_BER': dut_measured_ber,
                'PACKET_SIZE': es_vars['BER_PACKET_SIZE'],
                'PASS_FAIL': ber_pf
            }
        }
        
        return_data['DUT'].update(stats)
        return_data['DUT']['ERROR-SYMBOL-RECEIVED'] = symbol_error

        if self.link_partner.test_enabled == 'Enable':
            return_data['LP'] = self.link_partner.ethspy_link_get_stats()
            return_data['LP']['ERRORS'] = lp_errors
            return_data['LP']['GPRC'] = stats_lp['QR-GOOD-RECEIVES']
            return_data['LP']['MEASURED_BER'] = lp_measured_ber

        return return_data

    def compute_statistics(self, lst):
        """Compute the min, mean, max, mode, and mode frequency of lst and
        return the values as a dictionary.

        If lst does not have a min, mean, max, or unique mode, it will
        have None as the value for that particular statistic.

        :param list lst: A list containing values to compute statistics on
        :return: The statistics of lst
        :rtype: dict
        """
        output = {}
        clean_list = [
            x for x in lst if isinstance(x, int) or isinstance(x, float)
        ]

        if clean_list:
            output.update(self.stats_min(clean_list))
            output.update(self.stats_mean(clean_list))
            output.update(self.stats_max(clean_list))
            output.update(self.stats_stddev(clean_list))

        output.update(self.stats_mode(lst))

        return output

    def create_filename_check_path(self, ext):
        """Create the output file name from the DUT_NAME, the CHANNEL_NAME,
        and the LP_NAME.

        Args:
            ext ():

        Returns:
            str: The path and filename
        """
        file_path = os.path.normpath(
            '{}/{}_slot_{}/'.format(
                self.output_dir, self.dut.name, self.dut.slot_number
            )
        )

        try:
            channel_name = self.make_channel_name(
                self.channel, self.module_info
            )
        except AttributeError:
            channel_name = self.channel

        # Remove multiple whitespace characters and characters
        # problematic for filenames
        filename = '{}_{}_{}.{}'.format(
            self.dut.name, channel_name, self.link_partner.name, ext
        )
        filename = ' '.join(filename.split())
        # filename = ''.join([x if x.isalnum() or x in "._-()" else '_' for x in filename])

        path_and_file = os.path.join(file_path, filename)

        if not os.path.exists(os.path.dirname(path_and_file)):
            try:
                os.makedirs(os.path.dirname(path_and_file))
            except OSError as exc:  # Guard against a race condition
                if exc.errno != errno.EEXIST:
                    raise ethspylib.EthSpyError(
                        'Error creating directory! Ending script!'
                    )

        return path_and_file

    def check_max_filename_length(self):
        full_path = self.create_filename_check_path('json')

        if len(full_path) > 254:
            self.logger.info('Filename: ', full_path)
            print('Error: Filename and path too long!')
            raise ethspylib.EthSpyError('Error: Filename and path too long!')

    def csv_extract_data(self, data, padding, header=()):
        """Iterate through the dictionary, extracting the final list with
        the keys traversed given as header values.

        :param data:
        :param padding:
        :param header:
        :return:
        """
        data_list = []
        for key in data.keys():
            if isinstance(data[key], dict):
                returned_data = self.csv_extract_data(
                    data[key], padding, header=header + (key,)
                )
                data_list.extend(returned_data)
            elif isinstance(data[key], list):
                temp = []
                for _ in range(0, padding-len(header)):
                    temp.append('')
                for item in header:
                    temp.append(item)
                temp.append(key)
                temp.extend(data[key])
                data_list.append(temp)

        return data_list

    def csv_results(self, data, padding, header=()):
        """Iterate through the dictionary, extracting the final list with the
        keys traversed given as header values.

        :param data:
        :param padding:
        :param header:
        :return:
        """
        data_list = []
        for key in data.keys():
            if isinstance(data[key], dict):
                returned_data = self.csv_results(
                    data[key], padding, header=header + (key,)
                )
                data_list.extend(returned_data)
            else:
                temp = []
                for _ in range(0, padding - len(header)):
                    temp.append('')
                for item in header:
                    temp.append(item)
                temp.append(key)
                temp.append(data[key])
                data_list.append(temp)

        return data_list

    def disable_ehm_dnv(self):
        """THIS IS TO TEMPORARILY DISABLE EHM ON DNV UNTIL THAT
        FEATURE IS FULLY VALIDATED"""
        dut_snr_control = self.dut.snr_control
        lp_snr_control = self.link_partner.snr_control

        if self.dut.codename == 'Denverton':
            self.dut.snr_control = 'Disable'

        if self.link_partner.codename == 'Denverton':
            self.link_partner.snr_control = 'Disable'

        # ***INTERNAL***
        if self.dut.codename == 'Denverton':
            self.dut.snr_control = dut_snr_control

        if self.link_partner.codename == 'Denverton':
            self.link_partner.snr_control = lp_snr_control
        # ***INTERNAL***

        self.logger.info(
            'DUT SNR measurement {}d!'.format(self.dut.snr_control.lower())
        )
        self.logger.info(
            'LP SNR measurement {}d!\n'.format(self.link_partner.snr_control.lower())
        )

    def display_ber(self, delta_t, i, bit_rate, bit_tx_rate, lp_bit_rate, lp_bit_tx_rate, gprc, errors, ber_confidence):
        t_min, t_sec = divmod(delta_t, 60)

        timestamp = self.field_width(
            '{}:{}'.format(
                str(int(round2(t_min, 2))).zfill(2),
                str(int(round2(t_sec, 2))).zfill(2)
            ),
            7
        )
        iteration = self.field_width(
            '{}/{}'.format(str(i).zfill(3), str(self.link_attempts).zfill(3)),
            9
        )
        dut_slot = self.field_width(
            'DUT Slot = {}'.format(str(self.dut.slot)), 17
        )
        rate = self.field_width(
            'DUT RX Rate = {} Gbps'.format(str(round2(bit_rate, 1))), 17
        )
        tx_rate = self.field_width(
            'DUT TX Rate = {} Gbps'.format(str(round2(bit_tx_rate, 1))), 17
        )
        lp_rate = self.field_width(
            'Link Partner RX Rate = {} Gbps'.format(str(round2(lp_bit_rate, 1))), 17
        )
        lp_tx_rate = self.field_width(
            'Link Partner TX Rate = {} Gbps'.format(str(round2(lp_bit_tx_rate, 1))), 17
        )		
        good_rx = self.field_width(
            'GPRC = {} M'.format(
                '{0:.2f}'.format(round2(float(gprc) / 1.0e6, 2))), 17
        )
        rx_errors = self.field_width(
            '{} errors'.format(errors), 12
        )
        confidence_level = self.field_width(
            '{} CL = {}%'.format(self.ber_target, ber_confidence), 18
        )

        self.logger.info(
            '{}|{}| {} | {} | {} | {} | {} |{}|{}|{}|'.format(
                timestamp, iteration, dut_slot, tx_rate, rate, lp_tx_rate, lp_rate, good_rx, rx_errors, confidence_level
            )
        )

    def display_iteration(self, iteration):
        """Prints the current iteration, slot, and time to the screen."""

        self.logger.info(
            '-----------------------------------------------------------'
        )
        self.logger.info(
            'Starting iteration {} of {} on slot {} at {}'.format(
                iteration,
                self.link_attempts,
                self.dut.slot,
                time.strftime('%H:%M:%S', time.localtime())
            )
        )
        self.logger.info(
            '-----------------------------------------------------------'
        )

    def display_ehm(self, device, lane):
        # Output the EHM data to the screen
        # key - [list] all keys in dict
        # lst - [list] associated value of the key
        for key in self.data[device.id]['LANE'][lane].keys():
            lst = self.data[device.id]['LANE'][lane][key]
            try:
                self.logger.info(
                    '{} {} Lane{}: {} ( Min:{} | Mean:{} | Max:{} )\n'.format(
                        device.id,
                        key,
                        lane,
                        lst[-1],
                        self.minimum(lst),
                        self.mean(lst),
                        self.maximum(lst)
                    )
                )
            except (ValueError, AttributeError):
                self.logger.info('Unable to display EHM statistics!')
                
    def display_snr(self, device, lane):
        # Output the SNR data to the screen
        # key - [list] all keys in dict
        # lst - [list] associated value of the key
        for key in self.data[device.id]['SNR'][lane].keys():
            lst = self.data[device.id]['SNR'][lane][key]
            try:
                self.logger.info(
                    '{} {} Lane{}: {} ( Min:{} | Mean:{} | Max:{} )\n'.format(
                        device.id,
                        key,
                        lane,
                        lst[-1],
                        self.minimum(lst),
                        self.mean(lst),
                        self.maximum(lst)
                    )
                )
            except (ValueError, AttributeError):
                self.logger.info('Unable to display SNR statistics!')

    def display_ttl(self):
        # Output the TTL data to the screen
        try:
            for key in self.data[self.reset_side]['TTL'].keys():
                lst = self.data[self.reset_side]['TTL'][key]
                self.logger.info(
                    '{} {}: {} ( Min:{} | Mean:{} | Max:{} )'.format(
                        self.dut.id,
                        key,
                        lst[-1],
                        self.minimum(lst),
                        self.mean(lst),
                        self.maximum(lst)
                    )
                )
        except (ValueError, AttributeError):
            self.logger.info('Unable to display TTL statistics!')

        self.logger.info('\n')

    def dropped_packet_check(self, previously_dropped):
        self.logger.info('Checking for dropped packets...')
        if self.dut.codename == 'Linkville':
            time.sleep(200)
        time.sleep(10)
        self.link_partner.tx_rx_control('STOP')
        time.sleep(10)
        self.dut.tx_rx_control('STOP')
        time.sleep(10)

        rx_packets, _ = self.dut.get_qr_counter()
        tx_packets, _ = self.link_partner.get_qt_counter()

        dropped_packets = tx_packets - rx_packets

        if dropped_packets > 0 and dropped_packets != previously_dropped:
            self.logger.info(
                '{} packets were dropped!'.format(dropped_packets)
            )
            
            self.logger.info('Ending the BER test!')
            '''self.logger.info('Continuing the BER test!')

            self.dut.tx_rx_control('START')
            self.link_partner.tx_rx_control('START')'''
        else:
            dropped_packets = 0
            self.logger.info('No dropped packets detected!')
            self.logger.info('Ending the BER test!')

        return (dropped_packets + previously_dropped,
                dropped_packets - previously_dropped)

    def get_module_info(self, channel_info):
        # Determine if user the wants the channel name automatically populated
        if 'auto' in channel_info.lower():
            try:
                channel_info = self.dut.ethspy_module_info_get_all()
            except AttributeError:
                channel_info = {
                    'MODULE VENDOR': 'Unavailable',
                    'MODULE PN': 'Unavailable'
                }

        return channel_info

    def iteration_info(self, itr):
        """Displays and stores the current iteration information.

        Args:
            itr (int): The current LHC iteration.
        """
        self.display_iteration(itr)
        self.store_data(self.get_date_and_time(itr), self.data, ('ITERATION',))

    def run_lane_get_status(self, dev, lane):
        """Gets the lane status info from the provided device, stores the data and displays it.

        Args:
            dev (obj): A device to run the command on.
            lane (int): The lane to get the lane info from.

        Raises:
            AttributeError: The provided device is missing the required method.
        """
        try:
            self.store_data(dev.ethspy_lane_get_status(lane), self.data, (dev.id, 'LANE'))
        except AttributeError:
            pass

    def run_link_get_status(self, dev):
        """Gets the link status from the provided device and stores the data.

        Args:
            dev (obj): A device to run the command on.

        Raises:
            AttributeError: The provided device is missing the required method.
        """
        try:
            self.store_data(dev.ethspy_link_get_status(), self.data, (dev.id, 'LINK'))
        except AttributeError:
            pass

    def run_rx_get_ehm(self, dev, lane):
        """Gets the EHM info from the provided device, stores the data and displays it.

        TODO: This should only run on Snowridge devices. Snowridge should be refactored to include
          a rx_get_snr method.

        Args:
            dev (obj): A device to run the command on.
            lane (int): The lane to get the EHM info from.

        Raises:
            AttributeError: The provided device is missing the required method.
        """
        try:
            self.store_data(dev.ethspy_rx_get_ehm(lane), self.data, (dev.id, 'LANE', lane))
            self.display_ehm(dev, lane)
        except AttributeError:
            pass

    def run_rx_get_status(self, dev, lane):
        """Gets the Rx status info from the provided device, stores the data and displays it.

        Args:
            dev (obj): A device to run the command on.
            lane (int): The lane to get the Rx info from.

        Raises:
            AttributeError: The provided device is missing the required method.
        """
        try:
            self.store_data(dev.ethspy_rx_get_status(lane), self.data, (dev.id, 'RX', lane))
        except AttributeError:
            pass

    def run_snr(self, dev, lane, itr):
        """Gets the SNR information from the provided device, stores the data and displays it.

        Args:
            dev (obj): A device to run the command on.
            lane (int): The lane to get the SNR info from.
            itr (int): The current LHC iteration.
        """
        self.store_data(self.snr(dev, lane, itr), self.data, (dev.id, 'SNR', lane))
        #self.display_snr(dev, lane)

    def run_training_coeff_log(self, dev, lane, itr):
        """Gets the training coeff logs from the provided device and stores the data.

        Args:
            dev (obj): A device to run the command on.
            lane (int): The lane to get the logs on.
            itr (int): The current LHC iteration.

        Raises:
            AttributeError: The provided device is missing the required method.
        """
        try:
            self.store_data(
                self.training_coeff_log(dev.ethspy_rx_get_training_coeff_logs(lane), itr, dev.id),
                self.data,
                (dev.id, 'TRAINING_LOGS')
            )
        except AttributeError:
            pass

    def run_ttl(self):
        """Runs the TTL command and stores the data.

        Raises:
            AttributeError: The provided device is missing the required method.
        """
        try:
            self.store_data(self.ttl(self.retry_ttl), self.data, (self.reset_side, 'TTL'))
            self.display_ttl()
            self.logger.info('Waiting {} seconds for the link to settle...'.format(self.ttl_delay))
            time.sleep(self.ttl_delay)
        except AttributeError:
            pass

    def run_tx_get_status(self, dev, lane):
        """Gets the Tx status info from the provided device, stores the data and displays it.

        Args:
            dev (obj): A device to run the command on.
            lane (int): The lane to get the Tx info from.

        Raises:
            AttributeError: The provided device is missing the required method.
        """
        try:
            self.store_data(dev.ethspy_tx_get_status(lane), self.data, (dev.id, 'TX', lane))
        except AttributeError:
            pass

    def run_vbcm(self, device, iteration):
        # Get the calibration data
        cal_data = device.ethspy_rx_get_ehm_moncal_data()

        # Store the calibration data
        cal_archive = os.path.join(
            self.output_dir,
            'vbcm_raw_data',
            '{}_calibration_data_iteration_{}.csv'.format(device.id, iteration)
        )

        if not os.path.exists(os.path.dirname(cal_archive)):
            try:
                os.makedirs(os.path.dirname(cal_archive))
            except OSError:  # Guard against race condition
                print('Error creating directory! Ending script!')
                raise ethspylib.EthSpyError(
                    'Error creating directory! Ending script!'
                )

        with open(cal_archive, 'w') as archive_file:
            archive_file.write('{}'.format(cal_data))

        # Save the calibration data
        cal_file = os.path.join(
            'c:', '/', 'kerem_vbcm', 'mon_slc_calib_values.csv'
        )
        with open(cal_file, 'w') as cal_file_handle:
            cal_file_handle.write('{}'.format(cal_data))

        # Get the VBCM data
        csv_output = device.ethspy_rx_get_vbcm()

        # Need to create a temp file to store the data so we can process it
        temp_file = os.path.join(self.output_dir, 'temp.csv')
        with open(temp_file, 'w') as temp_fh:
            temp_fh.write('{}'.format(csv_output))

        # Now we strip out the inconsitent \r\n
        with open(os.path.join(self.output_dir, 'temp.csv'), 'r') as file_handle:
            cln_out = [cln_out for cln_out in file_handle.readlines() if cln_out.strip()]
            cln_out = [x.rstrip() for x in cln_out]

        # Create the final, clean, output file, in the location
        # expected by the EXE (c:/kerem_vbcm/vbcm.csv)
        exe_file = os.path.join('c:', '/', 'kerem_vbcm', 'vbcm.csv')

        with open(exe_file, 'w') as final_file:
            for line in cln_out:
                final_file.write('{}\n'.format(line))

        time.sleep(2)

        # Store the data from the vbcm output into a different file
        # since the above file gets overwritten each time
        vbcm_file_name = os.path.join(
            self.output_dir,
            'vbcm_raw_data',
            'raw_{}_vbcm_data_iteration_{}.csv'.format(device.id, iteration)
        )

        if not os.path.exists(os.path.dirname(vbcm_file_name)):
            try:
                os.makedirs(os.path.dirname(vbcm_file_name))
            except OSError:  # Guard against race condition
                print('Error creating directory! Ending script!')
                raise ethspylib.EthSpyError('Error creating directory! Ending script!')

        with open(vbcm_file_name, 'w') as file_handle:
            file_handle.write('{}'.format(csv_output))

        # Run the VBCM post-processor
        self.logger.info('Running the VBCM post-processor...')
        pp_args = [
            'c:/KEREM_VBCM/vbcm_exe_prw/vbcm_EHM12.exe',
            'c:/kerem_vbcm/vbcm.csv',
            'c:/kerem_vbcm/mon_slc_calib_values.csv',
            '""',
            '"1"',
            '""'
        ]
        subprocess.run(' '.join(pp_args), check=False)

        with open('c:/KEREM_VBCM/results.json', 'r') as results:
            try:
                snr = json.load(results)
            except ValueError:
                self.logger.info('Warning: Could not load VBCM results.')
                print('Warning: Could not load VBCM results.')
                snr = {}

        # Copy the output image
        try:
            file_util.copy_file(
                'c:/kerem_vbcm/vbcm.png',
                os.path.join(
                    self.output_dir,
                    'vbcm_raw_data',
                    '{}_vbcm_data_iteration_{}.png'.format(
                        device.id, iteration
                    )
                )
            )
        except OSError:
            self.logger.info('Warning: Problem copying VBCM PNG file.')
            print('Warning: Problem copying VBCM PNG file.')

        # Delete temporary files
        try:
            os.remove(temp_file)
        except OSError:
            self.logger.info('Warning: Could not delete {}.'.format(temp_file))
            print('Warning: Could not delete {}.'.format(temp_file))

        try:
            os.remove(exe_file)
        except OSError:
            self.logger.info('Warning: Could not delete {}.'.format(exe_file))
            print('Warning: Could not delete {}.'.format(exe_file))

        try:
            os.remove('c:/kerem_vbcm/vbcm.png')
        except OSError:
            self.logger.info('Warning: Could not delete vbcm.png')
            print('Warning: Could not delete vbcm.png')

        try:
            os.remove(cal_file)
        except OSError:
            self.logger.info('Warning: Could not delete {}.'.format(cal_file))
            print('Warning: Could not delete {}.'.format(cal_file))

        return snr

    def run_vbcm_pyc(self, device, iteration):
        two_levels_up = os.path.dirname(os.path.dirname(os.getcwd()))
        data_folder = os.path.join(two_levels_up, 'vbcm')
        pyc_post_proc = os.path.join(data_folder, 'vbcm_EHM12.pyc')

        win_python = os.path.join(
            two_levels_up,
            self.winpy_folder,
            self.winpy_exe_folder,
            'python.exe'
        )

        # Get the calibration data
        cal_data = device.ethspy_rx_get_ehm_moncal_data()

        if 'warning' in cal_data.lower():
            cal_flag = '""'
            cal_data_valid = False
            self.logger.info('Warning: Not using calibration data!')
            print('Warning: Not using calibration data!')
        else:
            cal_flag = '"1"'
            cal_data_valid = True

        # Save the calibration data
        cal_file = os.path.join(data_folder, 'calibration.csv')
        with open(cal_file, 'w') as cal_file_handle:
            cal_file_handle.write('{}'.format(cal_data))

        # Store the calibration data
        cal_archive = os.path.join(
            self.output_dir,
            'vbcm_raw_data',
            '{}_calibration_data_iteration_{}.csv'.format(device.id, iteration)
        )

        if not os.path.exists(os.path.dirname(cal_archive)):
            try:
                os.makedirs(os.path.dirname(cal_archive))
            except OSError:  # Guard against race condition
                print('Error creating directory! Ending script!')
                raise ethspylib.EthSpyError(
                    'Error creating directory! Ending script!'
                )

        with open(cal_archive, 'w') as archive_file:
            archive_file.write('{}'.format(cal_data))

        # Get the VBCM data
        csv_output = device.ethspy_rx_get_vbcm()

        if csv_output is None:
            return {
                'CalDataUsed': 'Error',
                'EHM12_NEG': 'Error',
                'EHM12_POS': 'Error',
                'LogBer': 'Error',
                'isResultValid': 'Error'
            }

        # Create a temp file to store the data so we can
        # process it (it will be deleted at the end of the method)
        vbcm_file = os.path.join(data_folder, 'vbcm.csv')
        with open(vbcm_file, 'w') as vbcm_fh:
            vbcm_fh.write('{}'.format(csv_output))

        time.sleep(2)

        # Store the data from the vbcm output into a different
        # file since the above file gets overwritten each time
        vbcm_file = os.path.join(
            self.output_dir,
            'vbcm_raw_data',
            'raw_{}_vbcm_data_iteration_{}.csv'.format(device.id, iteration)
        )

        if not os.path.exists(os.path.dirname(vbcm_file)):
            try:
                os.makedirs(os.path.dirname(vbcm_file))
            except OSError:  # Guard against race condition
                print('Error creating directory! Ending script!')
                raise ethspylib.EthSpyError(
                    'Error creating directory! Ending script!'
                )

        with open(vbcm_file, 'w') as file_handle:
            file_handle.write('{}'.format(csv_output))

        self.logger.info('Running the VBCM pyc post-processor...')
        args = [
            win_python,
            pyc_post_proc,
            vbcm_file,
            cal_file,
            cal_flag,
            '"1"',
            '""'
        ]
        proccess_complete = subprocess.run(' '.join(args), check=True)  # 0 = success, 1 = failure

        if proccess_complete.returncode == 0:
            with open(os.path.join(self.output_dir, 'vbcm_raw_data', 'results.json'), 'r') as res:
                try:
                    snr = json.load(res)
                    snr.update({'CalDataUsed': cal_data_valid})
                except ValueError:
                    self.logger.info(
                        'Warning: Could not load VBCM results.json file.'
                    )
                    print('Warning: Could not load VBCM results.json file.')
                    snr = {}
        else:
            snr = {}

        # Copy the output image
        img = os.path.join(
            self.output_dir,
            'vbcm_raw_data',
            '{}_vbcm_data_iteration_{}.png'.format(device.id, iteration)
        )
        if cal_data_valid:
            try:
                file_util.copy_file(
                    os.path.join(data_folder, 'vbcm_with_mon_calib.png'), img
                )
            except (OSError, DistutilsFileError):
                self.logger.info(
                    'Alert: Problem copying vbcm_with_mon_calib.png file.'
                )
        else:
            try:
                file_util.copy_file(os.path.join(data_folder, 'vbcm.png'), img)
            except (OSError, DistutilsFileError):
                self.logger.info('Alert: Problem copying vbcm.png file.')

        # Delete temporary files
        self.delete_file(vbcm_file)
        self.delete_file(os.path.join(data_folder, 'vbcm_with_mon_calib.png'))
        self.delete_file(cal_file)
        self.delete_file(os.path.join(data_folder, 'results.json'))

        return snr

    def set_packet_size(self):
        # Check to make sure the user entered correct information, fix if not
        if es_vars['speed'] == '1GBASET':
            self.set_packet_speed = '1G'
        elif es_vars['speed'] == '2.5GBASET':
            self.set_packet_speed = '2P5G'
        elif es_vars['speed'] == '5GBASET':
            self.set_packet_speed = '5G'
        elif es_vars['speed'] == '10GBASET':
            self.set_packet_speed = '10G'
        elif es_vars['speed'] == '25GBASET-CR1':
            self.set_packet_speed = '25G'
        elif es_vars['speed'] == '50GBASET-CR1':
            self.set_packet_speed = '50G'            
        elif es_vars['speed'] == '50GBASET-CR2':
            self.set_packet_speed = '50G'
        elif es_vars['speed'] == '100GBASET-CR2':
            self.set_packet_speed = '100G'
        elif es_vars['speed'] == '100GBASET-CR4':
            self.set_packet_speed = '100G'
        elif es_vars['speed'] == '200GBASET-CR4':
            self.set_packet_speed = '200G'
        #elif es_vars['speed'] == 'HSS_QSFP':
            #self.set_packet_speed = '100G'
        #elif es_vars['speed'] == 'HSS_SFP':
            #self.set_packet_speed = '100G'
        
        
        try:
            es_vars['BER_PACKET_SIZE'] = int(
                round2(float(es_vars['BER_PACKET_SIZE']), 2)
            )
        except ValueError:
            print('Error: BER_PACKET_SIZE is not an integer! Ending test!')
            raise ethspylib.EthSpyError(
                'Error: BER_PACKET_SIZE is not an integer! Ending test!'
            )

        es_vars['BER_PACKET_SIZE'] = self.dut.set_packet_size(
            self.set_packet_speed, es_vars['BER_PACKET_SIZE']
        )
        es_vars['BER_PACKET_SIZE'] = self.link_partner.set_packet_size(
            self.set_packet_speed, es_vars['BER_PACKET_SIZE']
        )
        
        return es_vars['BER_PACKET_SIZE']

    def snr(self, device, lane, iteration):
        if device.snr_control == 'Enable':
            if device.codename in ['Lewisberg', 'Denverton'] and self.winpy:
                snr = self.run_vbcm_pyc(device, iteration)
            else:
                snr = device.ethspy_rx_get_snr(5, lane=lane)
        else:
            snr = {'SNR': 'DISABLED'}

        return snr

    def static_device_info(self, device):
        # Store the output of the ETHSPY SUMMARY GET-STATUS command
        self.store_static_data(
            device.ethspy_summary_get_status(), self.data, (device.id, 'INFO')
        )
        self.store_static_data(
            device.version(), self.data, (device.id, 'INFO')
        )
        self.store_static_data(
            {'NAME': device.name}, self.data, (device.id, 'INFO')
        )
        self.store_static_data(
            {'CODENAME': device.codename}, self.data, (device.id, 'INFO')
        )

        # Store the output of the HOSTINFO command
        #if self.collect_hostinfo == 'Enable':
        #    self.store_static_data(
        #        device.hostinfo(), self.data, (device.id, 'HOSTINFO')
        #    )

    def statistics(self, dictionary, trail=()):

        # create a static list of the current dict keys
        # iterating directly over dict.keys() is bad bc
        # we are adding keys and the keys method returns
        # an iterator that will freak out if it gets bigger
        # during execution
        key_list = [i for i in dictionary.keys()]

        for key in key_list:
            if isinstance(dictionary[key], dict):
                self.statistics(dictionary[key], trail=trail + (key,))
            elif isinstance(dictionary[key], list):
                data = self.compute_statistics(dictionary[key])
                crumbs = ('RESULTS',) + trail + (key,)
                self.store_static_data(data, self.data, crumbs)

        return dictionary

        # temp_data = copy.copy(dictionary)
        # for key in dictionary.keys():
        #     if isinstance(dictionary[key], dict):
        #         dictionary[key] = self.statistics(dictionary[key], trail=trail + (key,))
        #     elif isinstance(dictionary[key], list):
        #         data = self.compute_statistics(dictionary[key])
        #         crumbs = ('RESULTS',) + trail + (key,)
        #         temp_data[key] = self.store_static_data(data, temp_data, crumbs)


        # self.data = copy.copy(temp_data)
        # import pprint
        # pp = pprint.PrettyPrinter(indent=4)
        # print('temp_data = ')
        # pp.pprint(temp_data)
        # print('\n\n')
        # print('self.data = ')
        # print(self.data)
        # print('\n\n')


        # return temp_data

    def store_data(self, new_data, container, nest):
        """Store data into the given structure at the location provided by nest.

        This method searches container for the first item in nest.

        If it is found, store_data is recursively called passing the
        sub-dictionary from container and trimming the first item from nest.

        If the first item in nest is not found in container, it is added and
        store_data is called recursively as above.

        If nest is empty, new_data is

        Args:
            new_data (dict): The data to be stored
            container (dict): The data structure that new_data is stored in
            nest (tuple): Keys to the location where new_data is stored

        Returns:

        """
        try:
            container = self.store_data(new_data, container[nest[0]], nest[1:])
        except KeyError:
            container[nest[0]] = {}
            container = self.store_data(new_data, container[nest[0]], nest[1:])
        except IndexError:
            container = self.append_data(new_data, container)

        return container

    def store_static_data(self, new_data, container, nest):
        try:
            container = self.store_static_data(
                new_data, container[nest[0]], nest[1:]
            )
        except KeyError:
            container[nest[0]] = {}
            container[nest[0]] = self.store_static_data(
                new_data, container[nest[0]], nest[1:]
            )
        except IndexError:
            container = self.add_static_data(new_data, container)

        return container

    def training_coeff_log(self, log, iteration, dut_lp):
        if log:
            log_file = os.path.join(
                self.output_dir,
                'training_logs',
                '{}_iteration_{}.json'.format(dut_lp, iteration)
            )

            if not os.path.exists(os.path.dirname(log_file)):
                try:
                    os.makedirs(os.path.dirname(log_file))
                except OSError as exc:  # Guard against race condition
                    if exc.errno != errno.EEXIST:
                        raise ethspylib.EthSpyError(
                            'Error creating directory! Ending script!'
                        )

            with open(log_file, 'w') as log_file_handle:
                log_file_handle.write(log)
        else:
            log_file = 'N/A'

        return {'TRAINING_LOGS': log_file}

    def ttl(self, retry_ttl):
        if retry_ttl:
            if self.reset_side == 'DUT':
                ttl_dict = self.dut.ethspy_link_get_ttl()
            else:
                ttl_dict = self.link_partner.ethspy_link_get_ttl()

            ttl_dict['RETRY_ATTEMPTS'] = self.retry_ttl - retry_ttl
            try:
                if ttl_dict['ERROR'] != 'None':
                    self.logger.info(
                        ('Alert: LINK GET-TTL encountered an error: {}. '
                         'Retrying up to {} more times.').format(
                             ttl_dict['ERROR'], (retry_ttl - 1)
                         )
                    )
                    self.logger.info(
                        'Waiting {} seconds for the link to settle...'.format(
                            self.ttl_delay
                        )
                    )
                    time.sleep(self.ttl_delay)
                    ttl_dict = self.ttl(retry_ttl=retry_ttl - 1)
            except KeyError:
                raise ethspylib.EthSpyError(
                    'Could not find ERROR key in TTL output! '
                    'Aborting current port!'
                )
        else:
            raise ethspylib.EthSpyError(
                'LINK GET-TTL retry limit hit! Aborting current port!'
            )

        return ttl_dict

    def write_comments_file(self, data):
        """Creates a comments file.

        If a comments section is found, a comments.txt file is written. If a comments section is not
            found, "No comments." is printed to the console.

        Args:
            data (dict): The dictionary to extract the comments from the "HW-INFO.COMMENTS" keys.
        """
        '''if data_comments := data.get('HW-INFO', {}).get('COMMENTS'):
            with open(self.create_filename_check_path('comments.txt'), 'w') as comments:
                comments.write('-----------------------------\n')
                comments.write('------ Comments info --------\n')
                comments.write('-----------------------------\n')

                comments.write(f"Comments: {data_comments}\n")
        else:
            print('No comments.')'''

    def write_csv_file(self, data):
        with open(self.create_filename_check_path('csv'), 'w') as file_handle:
            wtr = csv.writer(file_handle)

            headers = [('MODULE-INFO',), ('DUT', 'INFO'), ('LP', 'INFO')]
            padding = [0, 4, 4]
            for header, pad in zip(headers, padding):
                wtr.writerows(self.csv_static_info(data, header, pad))

            results = []
            try:
                results.extend(
                    self.csv_results(data['RESULTS'], 9, ('RESULTS',))
                )
                wtr.writerows(zip(*results))
            except KeyError:
                pass

            data_list = []
            for item in ['RESULTS', 'ITERATION', 'DUT', 'LP']:
                try:
                    data_list.extend(
                        self.csv_extract_data(data[item], 7, (item,))
                    )
                except KeyError:
                    pass
            wtr.writerows(zip(*data_list))

    def write_json_file(self, data):
        with open(self.create_filename_check_path('json'), 'w') as file_handle:
            json.dump(
                data, file_handle, sort_keys=False, indent=4, separators=(',', ': ')
            )

    def write_plain_text_file(self, data):
        with open(self.create_filename_check_path('txt'), 'w') as ptf:
            ptf.write('----------------------------\n')
            ptf.write('LHC Test Results\n')
            ptf.write('----------------------------\n')
            ptf.write(f"Date: {self.get_date_and_time(0)['DATE']}\n")
            ptf.write(f"Time: {self.get_date_and_time(0)['TIME']}\n\n")
            # ptf.write('System Name: {}\n\n'.format(socket.gethostname()))

            # Write the DUT information to the plain text file.
            dut_info = data['DUT']['INFO']
            try:
                ptf.write(f"DUT Name: {dut_info['NAME']}\n")

                if 'DEVICE-NAME' in dut_info:
                    ptf.write(f"LinkPartner Type: {dut_info['DEVICE-NAME']}\n")
                elif 'BRANDING_STRING' in dut_info:
                    ptf.write(f"DUT Type: {dut_info['BRANDING_STRING']}\n")
                else:
                    self.logger.info(
                        'Warning: Could not retrieve DEVICE-NAME or BRANDING_STRING from the DUT.'
                    )
                    print(
                        'Warning: Could not retrieve DEVICE-NAME or BRANDING_STRING from the DUT.'
                    )

                ptf.write(f"DUT Codename: {dut_info['CODENAME']}\n")

                if 'MAC-ADDRESS' in dut_info:
                    ptf.write(f"DUT MAC Address: {dut_info['MAC-ADDRESS']}\n")
                else:
                    ptf.write('DUT MAC Address: Unavailable\n')

                ptf.write(f"DUT EthAgent Version: {dut_info['ETHAGENT-VERSION']}\n")
                ptf.write(
                    "DUT PCIE Bus Device Function: {}:{}.{}\n\n".format(
                        dut_info['BUS'],
                        dut_info['DEVICE'],
                        dut_info['FUNCTION']
                    )
                )
            except KeyError:
                self.logger.info('Warning: Missing DUT information.')
                print('Warning: Missing DUT information.')

            # Write the Link Partner information to the plain text file.
            lp_info = data['LP']['INFO']
            try:
                ptf.write(f"LinkPartner Name: {lp_info['NAME']}\n")

                if 'DEVICE-NAME' in lp_info:
                    ptf.write(f"LinkPartner Type: {lp_info['DEVICE-NAME']}\n")
                elif 'BRANDING_STRING' in lp_info:
                    ptf.write(f"LinkPartner Type: {lp_info['BRANDING_STRING']}\n")
                else:
                    self.logger.info(
                        'Warning: Could not retrieve DEVICE-NAME or BRANDING_STRING from the LP.'
                    )
                    print(
                        'Warning: Could not retrieve DEVICE-NAME or BRANDING_STRING from the LP.'
                    )

                ptf.write(f"LinkPartner Codename:{lp_info['CODENAME']}\n")
                if 'MAC-ADDRESS' in lp_info:
                    ptf.write(f"LinkPartner MAC Address: {lp_info['MAC-ADDRESS']}\n")
                else:
                    ptf.write('LinkPartner MAC Address: Unavailable\n')
                ptf.write(f"LinkPartner EthAgent Version: {lp_info['ETHAGENT-VERSION']}\n")
                ptf.write("LinkPartner PCIE Bus Device Function: {}:{}.{}\n\n".format(
                    lp_info['BUS'],
                    lp_info['DEVICE'],
                    lp_info['FUNCTION']
                ))
            except KeyError:
                self.logger.info('Warning: Missing Link Partner information.')
                print('Warning: Missing Link Partner information.')

            if self.channel.lower() == 'auto':
                try:
                    ptf.write(
                        'Channel: {}_{}\n'.format(
                            data['MODULE-INFO']['VENDOR NAME'],
                            data['MODULE-INFO']['VENDOR PN']
                        )
                    )
                except KeyError:
                    ptf.write('Channel information unavailable')
            else:
                ptf.write(f"Channel: {self.channel}\n")

            try:
                ptf.write(
                    'The Bit Rate is: {}\n\n'.format(
                        data['RESULTS']['DUT']['LINK']['CURRENT-LINK-SPEED']['MODE']
                    )
                )
            except KeyError:
                self.logger.info('Could not retrieve bit rate information.')

            ptf.write('*** TTL Results ***\n')
            if 'TTL' in data['RESULTS']['DUT']:
                res = data['RESULTS']['DUT']['TTL']
            else:
                res = data['RESULTS']['LP']

            if 'MAC-TTL(ms)' in res:
                try:
                    ptf.write(f"Minimum TTL,{res['MAC-TTL(ms)']['MIN']} ms\n")
                    ptf.write(f"Mean TTL,{res['MAC-TTL(ms)']['MEAN']} ms\n")
                    ptf.write(f"Maximum TTL,{res['MAC-TTL(ms)']['MAX']} ms\n\n")
                except KeyError:
                    try:
                        ptf.write(f"Minimum TTL,{res['EXT-PHY-TTL(ms)']['MIN']} ms\n")
                        ptf.write(f"Mean TTL,{res['EXT-PHY-TTL(ms)']['MEAN']} ms\n")
                        ptf.write(f"Maximum TTL,{res['EXT-PHY-TTL(ms)']['MAX']} ms\n\n")
                    except KeyError:
                        self.logger.info('Warning: Could not retrieve TTL data.')
                        print('Warning: Could not retrieve TTL data.')

            elif 'LINK TTL(MS)' in res:
                ptf.write(f"Minimum TTL,{res['LINK TTL(MS)']['MIN']} ms\n")
                ptf.write(f"Mean TTL,{res['LINK TTL(MS)']['MEAN']} ms\n")
                ptf.write(f"Maximum TTL,{res['LINK TTL(MS)']['MAX']} ms\n\n")
            else:
                self.logger.info('Warning: Could not retrieve TTL data.')
                print('Warning: Could not retrieve TTL data.')

            # Timing for last bucket is irrelevant because it gets all items not in other buckets
            # BASE-T uses pass/fail buckets with no distribution
            if self.dut.interface == 'base_t':
                limits = [100, 0]
                speed = self.dut.get_speed()
                if speed == '10G':
                    timing = [30, 50]
                elif speed == '5G':
                    timing = [30, 50]
                elif speed == '2.5G':
                    timing = [30, 50]
                elif speed == '1G':
                    timing = [12, 50]
                elif speed == '100M':
                    timing = [10, 50]
                else:
                    self.logger.info('Warning: Could not process BASE-T Speed for TTL: ' + speed)
                    print('Warning: Could not process BASE-T Speed: ' + speed)
                    timing = [30, 50]
            elif self.dut.interface == 'hss':
                limits = [80, 10, 10, 0]
                timing = [1, 2, 3, 4]
            else:
                self.logger.info('Warning: Could not process interface under test for TTL.')
                print('Warning: Could not process interface under test for TTL.')
                limits = [80, 10, 10, 0]
                timing = [1, 2, 3, 4]

            ttl_percentages, ttl_statuses = self.ttl_post_processor(data, timing, limits)
            last_num = len(timing) - 1
            ptf.write(
                'TTL < {}s, {}%, ({})\n'.format(
                    timing[0], ttl_percentages[0], ttl_statuses[0]
                )
            )
            for num in range(1, last_num):
                ptf.write(
                    '{}s < TTL < {}s, {}%, ({})\n'.format(
                        timing[num-1], timing[num], ttl_percentages[num], ttl_statuses[num]
                    )
                )
            ptf.write(
                '{}s < TTL, {}%, ({})\n'.format(
                    timing[last_num-1], ttl_percentages[last_num], ttl_statuses[last_num]
                )
            )

            ptf.write(self.ber_post_processor(data))

            for device in [self.dut, self.link_partner]:
                if device.codename not in ('Columbiaville', 'COLUMBIA PARK', 'Snowridge'):
                    ptf.write(self.snr_post_processor(device, data))

    def ber_compute_confidence_level(self, errors, bits):
        step1 = 0
        for k in range(0, errors + 1):
            try:
                step1 += (
                    pow((bits * float(self.ber_target)), k) / math.factorial(k)
                )
            except OverflowError:
                self.logger.info(
                    'Warning: OverflowError detected during '
                    'BER confidence level calculation.'
                )
                print(
                    'Warning: OverflowError detected during '
                    'BER confidence level calculation.'
                )
                break

        step2 = (1 - (step1 * math.exp(-bits * float(self.ber_target)))) * 100

        return float('{0:.1f}'.format(step2))

    @staticmethod
    def ber_pass_fail(measurement):
        pass_fail = 'FAIL'

        try:
            if round2(measurement, 2) >= es_vars['BER_CONFIDENCE']:
                pass_fail = 'PASS'
        except TypeError:
            pass

        return pass_fail

    def ber_post_processor(self, data_dict):
        statuses = ['FAIL', 'FAIL', 'FAIL']
        output_string = ''

        try:
            percentages = [data_dict['RESULTS']['DUT']['BER']['CONFIDENCE']['MIN'],
                           data_dict['RESULTS']['DUT']['BER']['CONFIDENCE']['MEAN'],
                           data_dict['RESULTS']['DUT']['BER']['CONFIDENCE']['MAX']]

            for val in range(0, 3):
                if percentages[val] >= es_vars['BER_CONFIDENCE']:
                    statuses[val] = 'PASS'

            output_string += '*** BER Confidence Results ***\n'
            output_string += 'Minimum BER Confidence, {:.2f}%, ({})\n'.format(
                percentages[0], statuses[0]
            )
            output_string += 'Mean BER Confidence, {:.2f}%, ({})\n'.format(
                percentages[1], statuses[1]
            )
            output_string += 'Maximum BER Confidence, {:.2f}%, ({})\n'.format(
                percentages[2], statuses[2]
            )
            output_string += '\n'

        except KeyError:
            self.logger.info('Warning: Error retrieving BER confidence data.')
            print('Warning: Error retrieving BER confidence data.')

        return output_string

    def castes_vars(self):
        # Cast the the expected EthSpy number variables as integers
        # here to make the code less messy everywhere else
        try:
            # es_vars['LINK_ITERATIONS'] = int(es_vars['LINK_ITERATIONS'])
            # es_vars['BER_ITERATIONS'] = int(es_vars['BER_ITERATIONS'])
            es_vars['BER_THRESHOLD'] = int(es_vars['BER_THRESHOLD'])
            es_vars['BER_TIMEOUT'] = int(es_vars['BER_TIMEOUT'])
            es_vars['BER_ERROR_THRESHOLD'] = int(
                es_vars['BER_ERROR_THRESHOLD']
            )
        except Exception as err:
            self.logger.info(err)
            raise ethspylib.EthSpyError(
                'Could not cast variable! Ending script!'
            )

    def check_confidence_level(self):
        es_vars['BER_CONFIDENCE'] = int(
            round2(float(es_vars['BER_CONFIDENCE']), 2)
        )
        if es_vars['BER_CONFIDENCE'] < 0:
            self.logger.info(
                'BER confidence level of {} is out of range!'.format(
                    es_vars['BER_CONFIDENCE']
                )
            )
            self.logger.info('Changing BER confidence level to 0.')
            es_vars['BER_CONFIDENCE'] = 1
        elif es_vars['BER_CONFIDENCE'] > 99:
            self.logger.info(
                'BER confidence level of {} is out of range!'.format(
                    es_vars['BER_CONFIDENCE']
                )
            )
            self.logger.info('Changing BER confidence level to 99.')
            es_vars['BER_CONFIDENCE'] = 99

    def check_link(self, link_status):
        """Checks if the link is down.

        Outputs a message to the log if the link is down and ends the script with an error.

        Args:
            link_status (str): The status of the link, either UP or DOWN.

        Raises:
            ethspylib.EthSpyError: Error is raised if link is down, ending the script.
        """
        if link_status == 'DOWN':
            self.logger.info(
                'Link is down! Make sure you have a cable '
                'plugged into the DUT and link partner!'
            )
            self.logger.info('Ending script!')
            raise ethspylib.EthSpyError(
                'No link! Make sure you have a cable plugged '
                'into the DUT and link partner! Ending script!'
            )

    @staticmethod
    def csv_static_info(data, keys, padding):
        new_pad = padding + 1
        data_list = []
        data_copy = data

        try:
            for key in keys:
                data_copy = data_copy[key]

            for key in sorted(data_copy.keys()):
                temp = []
                for _ in range(0, new_pad - len(keys)):
                    temp.append('')
                for item in keys:
                    temp.append(item)
                temp.append(key)
                temp.append(data_copy[key])
                data_list.append(temp)

            return zip(*data_list)
        except KeyError:
            return []

    def delete_file(self, filename):
        try:
            os.remove(filename)
        except OSError:
            self.logger.info('Alert: Could not delete {}.'.format(filename))

    @staticmethod
    def field_width(val, width):
        """Pad a string with spaces so it is centered in width and return
        the padded string.

        :param str val: The string to center
        :param int width: The width of the field to center the string in
        :return: val if string is longer than width or val centered in width
        :rtype: str

        .. todo:: I believe the Python string format statement has this capability, should
           investigate and update this method.

        """
        if len(val) > width:
            ret_val = val
        else:
            leftover = width - len(val)
            if leftover % 2:
                front_pad = (leftover // 2) + 1
                back_pad = leftover // 2
            else:
                front_pad = leftover // 2
                back_pad = front_pad

            front_str = ' ' * front_pad
            back_str = ' ' * back_pad

            ret_val = front_str + val + back_str

        return ret_val

    @staticmethod
    def find_winpython():
        found = False
        winpy_folder = None
        winpy_exe_folder = None

        search_folder = os.path.dirname(os.path.dirname(os.getcwd()))
        folders = os.listdir(search_folder)

        for folder in folders:
            if 'winpy' in folder.lower():
                found = True
                winpy_folder = folder

        if found:
            sub_search_folder = os.listdir(
                os.path.join(search_folder, winpy_folder)
            )
            for sub_folder in sub_search_folder:
                if 'python-2' in sub_folder.lower():
                    winpy_exe_folder = sub_folder

        return found, winpy_folder, winpy_exe_folder

    @staticmethod
    def get_date_and_time(iteration):
        """Get the current date and time and return it in a dictionary.

        :return: Current date and time information
        :rtype: dictionary
        """
        current_time = time.localtime()
        iteration_data = {
            'DATE': time.strftime('%m/%d/%Y', current_time),
            'TIME': time.strftime('%H:%M:%S', current_time),
            'ITERATION': iteration
        }

        return iteration_data

    @staticmethod
    def make_channel_name(chan, info):
        # Determine if user wants channel name to be automatically populated
        if 'auto' in chan.lower():
            # Strip off 'auto_' from the channel name and keep the rest of
            # the characters in the string
            add_on = chan[5:]
            chan = " ".join([info['VENDOR NAME'], info['VENDOR PN'], add_on])
            chan = chan.replace('_', ' ')
            chan = chan.split()
            chan = '_'.join(chan)
        return chan

    @staticmethod
    def mean(lst):
        """Remove all non-numerical values from lst and compute the mean of
        the resulting list.

        Args:
            lst (list): The list to compute the mean of.
        :return:
        """
        clean_list = [x for x in lst if isinstance(x, (float, int))]

        avg = float(sum(clean_list)) / max(len(clean_list), 1)

        if len(clean_list) == 0:
            avg = None

        return avg

    @staticmethod
    def minimum(lst):
        clean_list = [x for x in lst if isinstance(x, (float, int))]

        try:
            min_val = min(clean_list)
        except (ValueError, TypeError):
            min_val = None

        return min_val

    @staticmethod
    def maximum(lst):
        clean_list = [x for x in lst if isinstance(x, (float, int))]

        try:
            max_val = max(clean_list)
        except (ValueError, TypeError):
            max_val = None

        return max_val

    @staticmethod
    def sum_rcv_errors(data, sym_err):
        error_sum = 0

        if 'QR-RECEIVE-ERRORS' in data:
            error_sum += int(data['QR-RECEIVE-ERRORS'])

        if 'ERROR-SYMBOL-RECEIVED' in data:
            if data['ERROR-SYMBOL-RECEIVED']:
                error_sum += 1
                sym_err = True

        return error_sum, sym_err

    def stats_max(self, lst):
        return {'MAX': self.maximum(lst)}

    @staticmethod
    def stats_mean(lst):
        """Mean of the resulting list.

        Args:
            lst (list): The list to compute the mean of.

        Returns:
            dict: Mapping the key MEAN to the mean value of the list.
        """
        return {'MEAN': float(sum(lst)) / max(len(lst), 1)}

    def stats_min(self, lst):
        """Gets the minimum value in the list.
        """
        return {'MIN': self.minimum(lst)}

    @staticmethod
    def stats_mode(lst):
        try:
            data = Counter(lst)
            results = data.most_common()

            try:
                if results[0][1] == results[1][1]:
                    r_val = {'MODE': 'None', 'MODE_OCCURRENCES': 'None'}
                else:
                    r_val = {
                        'MODE': results[0][0],
                        'MODE_OCCURRENCES': results[0][1]
                    }
            except IndexError:
                try:
                    r_val = {
                        'MODE': results[0][0],
                        'MODE_OCCURRENCES': results[0][1]
                    }
                except IndexError:
                    r_val = {
                        'MODE': 'Could not calculate',
                        'MODE_OCCURENCES': 'Could not calculate'
                    }
        except TypeError:
            r_val = {'MODE': 'None', 'MODE_OCCURRENCES': 'None'}

        return r_val

    @staticmethod
    def stats_stddev(lst):
        mean = float(sum(lst)) / len(lst)
        variance = sum([(x - mean)**2 for x in lst]) / float(len(lst))
        output = {'STDDEV': math.sqrt(variance)}

        return output

    def snr_post_processor(self, device, data):
        distribution = {
            'Broadwell': [27, 16],
            'Carlsville': [0, 0],
            'Columbiaville': [40, 20],
            'Coppervale': [4, 2],
            'Denverton': [36, 25],
            'Fortville': [40, 20],
            'Fortville25': [40, 20],
            'Foxville': [4, 2],
            'Lewisberg': [36, 25],
            'Niantic': [17, 16],
            'Parkvale': [40, 20],
            'Powerville': [0, 0],
            'RedRockCanyon': [40, 20],
            'Sageville': [4, 2],
            'Twinville': [0, 0]
        }
        testids = [
            'results over {}'.format(distribution[device.codename][0]),
            'results between {} and {}'.format(
                distribution[device.codename][0],
                distribution[device.codename][1]
            ),
            'results below {}'.format(distribution[device.codename][1])
        ]
        output_string = ''

        try:
            if device.snr_type[0] in data[device.id]['SNR'][0]:
                snr_strings = device.snr_type
            else:
                snr_strings = data[device.id]['SNR'][0]
        except KeyError:
            self.logger.info('Could not retrieve SNR information.')
            return output_string

        for lane in range(0, len(data[device.id]['SNR'])):
            output_string += '\n*** {} LANE {} - {} ***'.format(
                device.id, lane, es_vars['DUT_NAME']
            )

            for snr_type in snr_strings:
                buckets = [[], [], []]
                percentages = [0, 0, 0]

                try:
                    if data['RESULTS'][device.id]['SNR'][lane][snr_type]['MIN'] >= distribution[device.codename][0]:
                        risk = 'a LOW'
                    elif distribution[device.codename][0] > data['RESULTS'][device.id]['SNR'][lane][snr_type]['MIN'] >= distribution[device.codename][1]:
                        risk = 'an INCONCLUSIVE'
                    else:
                        risk = 'a HIGH'
                except KeyError:
                    risk = 'an UNKNOWN'

                output_string += '\nThis design has {} amount of risk.\n\n'.format(risk)

                # Note that these are pulling from the RESULTS key, not the raw data
                try:
                    output_string += 'Minimum {}, {}{}\n'.format(
                        snr_type,
                        round2(data['RESULTS'][device.id]['SNR'][lane][snr_type]['MIN'], 1),
                        device.snr_unit_of_measure
                    )
                    output_string += 'Mean {}, {}{}\n'.format(
                        snr_type,
                        round2(data['RESULTS'][device.id]['SNR'][lane][snr_type]['MEAN'], 1),
                        device.snr_unit_of_measure
                    )
                    output_string += 'Maximum {}, {}{}\n\n'.format(
                        snr_type,
                        round2(data['RESULTS'][device.id]['SNR'][lane][snr_type]['MAX'], 1),
                        device.snr_unit_of_measure
                    )
                except KeyError:
                    output_string += f'No {snr_type} statistics data available.\n\n'
                else:
                    for result in data[device.id]['SNR'][lane][snr_type]:
                        # These are being pulled from the raw data, not the RESULTS
                        if result not in ('DISABLED', 'ERROR', 'NA', 'N/A'):
                            if result >= distribution[device.codename][0]:
                                buckets[0].append(result)
                            elif result <= distribution[device.codename][1]:
                                buckets[1].append(result)
                            else:
                                buckets[2].append(result)

                    if device.snr_control == 'Enable':
                        for val in range(0, 3):
                            percentages[val] = 100 * ((len(buckets[val])) * 1.0 / len(data[device.id]['SNR'][lane][snr_type]))

                        for tid, per in zip(testids, percentages):
                            output_string += '{} {}, {}%\n'.format(
                                snr_type, tid, round2(per, 1)
                            )

            # output_string += '\n\n'

        output_string += '\n'

        return output_string

    def ttl_post_processor(self, dict_data, timing, limits):
        # TTL PASS/FAIL Criteria:
        # 80% <= 1s
        # 10% <= 2s
        # 10% <= 3s
        #  0% >  4s
        percentages = [0 for i in range(len(timing))]
        statuses = ['FAIL' for i in range(len(timing))]
        buckets = [[] for i in range(len(timing))]
        side = ""

        if len(timing) != len(limits):
            self.logger.info('Warning: Could not compute TTL distribution. Invalid limit inputs.')
            print('Warning: Could not compute TTL distribution. Invalid limit inputs.')
            return percentages, statuses

        if 'TTL' in dict_data['DUT']:
            side = 'DUT'
        else:
            side = 'LP'

        # Get the TTL data... the except clause was needed for Foxville.
        try:
            if 'MIN' not in dict_data['RESULTS'][side]['TTL']['MAC-TTL(ms)']:
                ttl_data = dict_data[side]['TTL']['EXT-PHY-TTL(ms)']
            else:
                ttl_data = dict_data[side]['TTL']['MAC-TTL(ms)']
        except KeyError:
            ttl_data = dict_data[side]['TTL']['LINK TTL(MS)']

        for item in ttl_data:
            flag = False
            for i in range(len(timing)-1):
                if item <= timing[i] * 1000:
                    buckets[i].append(item)
                    flag = True
                    break

            # Handle out of range case
            if not flag:
                buckets[len(timing)-1].append(item)

        for val in range(0, len(timing)):
            percentages[val] = 100 * ((len(buckets[val]) * 1.0) / len(ttl_data))
            if percentages[val] <= limits[val] and val > 0:
                statuses[val] = 'PASS'

        if percentages[0] >= limits[0]:
            statuses[0] = 'PASS'

        return percentages, statuses

    def save_eeprom(self, device):
        file_and_path = os.path.join(
            self.output_dir,
            '{}_EEPROM_CONTENTS_{}.txt'.format(device.name, time.strftime('%Y%m%d_%H%M%S'))
        )
        with open(file_and_path, 'w') as file_handle:
            data = device.reep().split('\n')
            for line in data:
                file_handle.write(line.strip())
                file_handle.write('\n')
