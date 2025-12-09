import sys
from subprocess import call
import logging
import datetime
import ANIL_Robot_LHC_Auto_Config as test_cofig
str_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
sys.path.append('.')
from ethspylib import *
import socket
import os, shutil
from subprocess import call
from pathlib import Path
import builtins as __builtin__
import glob
__builtin__._ETHSPY_VARS = {}

import tkinter as tk
from tkinter import filedialog as fd
'''
class filedialog(tk.Tk):
    @classmethod
    def askopenfilename(cls, *args, **kwargs):
        root = cls()
        root.wm_withdraw()
        files = fd.askopenfilename(*args, **kwargs)
        root.destroy()
        return files
Cable_Lengths_File = filedialog.askopenfilename()'''

''' Output File Config Start'''
Output_path=test_cofig.Output_path
Output_folder_Prefix = test_cofig.Output_folder_Prefix
''' Output File Config End'''
SAVE_PATH = Output_path + Output_folder_Prefix + test_cofig.speed +'_' + str_time
if not os.path.exists(SAVE_PATH):
    os.makedirs(SAVE_PATH)
__builtin__._ETHSPY_VARS['OUTPUT_DIR'] = SAVE_PATH

file_path = SAVE_PATH + "\\Output.log"
EA_log_file_path = SAVE_PATH + "\\EthAgent.log"
#os.remove(file_path)
logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level
    format='%(asctime)s - %(message)s',  # Set the format for log messages
    handlers=[
        logging.FileHandler(file_path),  # Log to a file
        logging.StreamHandler()  # Also log to console
    ]
)

logger = logging.getLogger(__name__)

logger2 = logging.getLogger('EA_log')
if test_cofig.EthAgent_command == 'Enable':
    logger2.addHandler(logging.FileHandler(EA_log_file_path))

logger.info('----------------------------------------')
logger.info('BER Testing result save to - {}'.format(SAVE_PATH))
logger.info('----------------------------------------')


logger.info('----------------------------------------')
logger.info('Initializing all devices ...')
logger.info('----------------------------------------')
''' Test Config Start'''

__builtin__._ETHSPY_VARS['speed'] = test_cofig.speed
__builtin__._ETHSPY_VARS['cable_type'] = test_cofig.cable_type
__builtin__._ETHSPY_VARS['com_port'] = test_cofig.com_port
__builtin__._ETHSPY_VARS['parallel'] = test_cofig.parallel
#__builtin__._ETHSPY_VARS['lengths_file'] = Cable_Lengths_File
__builtin__._ETHSPY_VARS['cable_length'] = test_cofig.cable_length
__builtin__._ETHSPY_VARS['link_iterations'] = test_cofig.link_iterations
__builtin__._ETHSPY_VARS['reset_side'] = test_cofig.reset_side
__builtin__._ETHSPY_VARS['ttl_delay'] = test_cofig.ttl_delay
__builtin__._ETHSPY_VARS['ber_iterations'] = test_cofig.ber_iterations

__builtin__._ETHSPY_VARS['dut0_enable'] = test_cofig.dut0_enable
__builtin__._ETHSPY_VARS['dut0'] = Port(test_cofig.dut0_ip,test_cofig.dut0_slot,logger,logger2)
__builtin__._ETHSPY_VARS['dut0_name'] = test_cofig.dut0_name
__builtin__._ETHSPY_VARS['lp0'] = Port(test_cofig.lp0_ip,test_cofig.lp0_slot,logger,logger2)
__builtin__._ETHSPY_VARS['lp0_name'] = test_cofig.lp0_name

__builtin__._ETHSPY_VARS['dut1_enable'] = test_cofig.dut1_enable
__builtin__._ETHSPY_VARS['dut1'] = Port(test_cofig.dut1_ip,test_cofig.dut1_slot,logger,logger2)
__builtin__._ETHSPY_VARS['dut1_name'] = test_cofig.dut1_name
__builtin__._ETHSPY_VARS['lp1'] = Port(test_cofig.lp1_ip,test_cofig.lp1_slot,logger,logger2)
__builtin__._ETHSPY_VARS['lp1_name'] = test_cofig.lp1_name

__builtin__._ETHSPY_VARS['dut2_enable'] = test_cofig.dut2_enable
__builtin__._ETHSPY_VARS['dut2'] = Port(test_cofig.dut2_ip,test_cofig.dut2_slot,logger,logger2)
__builtin__._ETHSPY_VARS['dut2_name'] = test_cofig.dut2_name
__builtin__._ETHSPY_VARS['lp2'] = Port(test_cofig.lp2_ip,test_cofig.lp2_slot,logger,logger2)
__builtin__._ETHSPY_VARS['lp2_name'] = test_cofig.lp2_name

__builtin__._ETHSPY_VARS['dut3_enable'] = test_cofig.dut3_enable
__builtin__._ETHSPY_VARS['dut3'] = Port(test_cofig.dut3_ip,test_cofig.dut3_slot,logger,logger2)
__builtin__._ETHSPY_VARS['dut3_name'] = test_cofig.dut3_name
__builtin__._ETHSPY_VARS['lp3'] = Port(test_cofig.lp3_ip,test_cofig.lp3_slot,logger,logger2)
__builtin__._ETHSPY_VARS['lp3_name'] = test_cofig.lp3_name

__builtin__._ETHSPY_VARS['dut4_enable'] = test_cofig.dut4_enable
__builtin__._ETHSPY_VARS['dut4'] = Port(test_cofig.dut4_ip,test_cofig.dut4_slot,logger,logger2)
__builtin__._ETHSPY_VARS['dut4_name'] = test_cofig.dut4_name
__builtin__._ETHSPY_VARS['lp4'] = Port(test_cofig.lp4_ip,test_cofig.lp4_slot,logger,logger2)
__builtin__._ETHSPY_VARS['lp4_name'] = test_cofig.lp4_name

__builtin__._ETHSPY_VARS['dut5_enable'] = test_cofig.dut5_enable
__builtin__._ETHSPY_VARS['dut5'] = Port(test_cofig.dut5_ip,test_cofig.dut5_slot,logger,logger2)
__builtin__._ETHSPY_VARS['dut5_name'] = test_cofig.dut5_name
__builtin__._ETHSPY_VARS['lp5'] = Port(test_cofig.lp5_ip,test_cofig.lp5_slot,logger,logger2)
__builtin__._ETHSPY_VARS['lp5_name'] = test_cofig.lp5_name

__builtin__._ETHSPY_VARS['dut6_enable'] = test_cofig.dut6_enable
__builtin__._ETHSPY_VARS['dut6'] = Port(test_cofig.dut6_ip,test_cofig.dut6_slot,logger,logger2)
__builtin__._ETHSPY_VARS['dut6_name'] = test_cofig.dut6_name
__builtin__._ETHSPY_VARS['lp6'] = Port(test_cofig.lp6_ip,test_cofig.lp6_slot,logger,logger2)
__builtin__._ETHSPY_VARS['lp6_name'] = test_cofig.lp6_name

__builtin__._ETHSPY_VARS['dut7_enable'] = test_cofig.dut7_enable
__builtin__._ETHSPY_VARS['dut7'] = Port(test_cofig.dut7_ip,test_cofig.dut7_slot,logger,logger2)
__builtin__._ETHSPY_VARS['dut7_name'] = test_cofig.dut7_name
__builtin__._ETHSPY_VARS['lp7'] = Port(test_cofig.lp7_ip,test_cofig.lp7_slot,logger,logger2)
__builtin__._ETHSPY_VARS['lp7_name'] = test_cofig.lp7_name
''' Test Config End'''

if __builtin__._ETHSPY_VARS['dut0_enable'] == 'Enable':
    __builtin__._ETHSPY_VARS['dut0'].open_auto()
    __builtin__._ETHSPY_VARS['lp0'].open_auto()

if __builtin__._ETHSPY_VARS['dut1_enable'] == 'Enable':
    __builtin__._ETHSPY_VARS['dut1'].open_auto()
    __builtin__._ETHSPY_VARS['lp1'].open_auto()

if __builtin__._ETHSPY_VARS['dut2_enable'] == 'Enable':
    __builtin__._ETHSPY_VARS['dut2'].open_auto()
    __builtin__._ETHSPY_VARS['lp2'].open_auto()

if __builtin__._ETHSPY_VARS['dut3_enable'] == 'Enable':
    __builtin__._ETHSPY_VARS['dut3'].open_auto()
    __builtin__._ETHSPY_VARS['lp3'].open_auto()

if __builtin__._ETHSPY_VARS['dut4_enable'] == 'Enable':
    __builtin__._ETHSPY_VARS['dut4'].open_auto()
    __builtin__._ETHSPY_VARS['lp4'].open_auto()
    
if __builtin__._ETHSPY_VARS['dut5_enable'] == 'Enable':
    __builtin__._ETHSPY_VARS['dut5'].open_auto()
    __builtin__._ETHSPY_VARS['lp5'].open_auto()

if __builtin__._ETHSPY_VARS['dut6_enable'] == 'Enable':
    __builtin__._ETHSPY_VARS['dut6'].open_auto()
    __builtin__._ETHSPY_VARS['lp6'].open_auto()

if __builtin__._ETHSPY_VARS['dut7_enable'] == 'Enable':
    __builtin__._ETHSPY_VARS['dut7'].open_auto()
    __builtin__._ETHSPY_VARS['lp7'].open_auto()

"""This module provides functionality to control the robot to perform Base-T testing."""
# Standard library imports
import json
import os
import threading
import time
import traceback

# Local project imports
from devices.common.device_init import DeviceInit
import ANILRobotController
import LHC
import anil_robot_config


class RobotLHCWrapper:
    """This class performs BER testing on Base-T products using the robot."""

    def __init__(self,logger):
        """Initialize the object with some default LHC values."""
        self.es_vars = _ETHSPY_VARS
        self.ber_iterations = int(self.es_vars['ber_iterations'])
        self.link_iterations = int(self.es_vars['link_iterations'])
        self.ttl_delay = int(self.es_vars['ttl_delay'])
        self.speed = self.es_vars['speed']
        self.retry_ttl = 5

        # I have all the speeds broken out because we are going to tweak the
        # values for each once we get more experience with how long each takes.
        if self.speed == '1GBASET':
            self.es_vars['BER_TIMEOUT'] = 60
        elif self.speed == '2.5GBASET':
            self.es_vars['BER_TIMEOUT'] = 2400
        elif self.speed == '5GBASET':
            self.es_vars['BER_TIMEOUT'] = 1200
        elif self.speed == '10GBASET':
            self.es_vars['BER_TIMEOUT'] = 600
        else:
            self.es_vars['BER_TIMEOUT'] = 600

        self.es_vars['BER_CONFIDENCE'] = 95
        self.es_vars['BER_ERROR_THRESHOLD'] = 20
        self.es_vars['BER_PACKET_SIZE'] = 1518
        self.es_vars['BER_THRESHOLD'] = -1000000
        self.es_vars['DUT_SNR_CONTROL'] = 'Enable'
        self.es_vars['LP_DATA'] = 'Enable'
        self.es_vars['LP_SNR_CONTROL'] = 'Enable'
        self.es_vars['RESET_SIDE'] = test_cofig.reset_side
        self.es_vars['COLLECT_HOSTINFO'] = 'Enable'
        self.es_vars['DROPPED_PACKETS'] = 'Enable'
        self.es_vars['DUT_EEPROM_DUMP'] = 'Disable'
        self.es_vars['LP_EEPROM_DUMP'] = 'Disable'

        self.logger = logger
        if test_cofig.bypass_robot == 'Disable':
            self.robot = ANILRobotController.ANILRobot(self.es_vars['com_port'],logger)
        self.dev_init = DeviceInit(logger)
        self.scoreboard = [False, False, False, False]
        self.head_position = ''

        self.dut_ports = []
        self.dut_names = []
        self.lp_ports = []
        self.lp_names = []

        self.enabled_ports = [
            self.es_vars['dut0_enable'], self.es_vars['dut1_enable'],
            self.es_vars['dut2_enable'], self.es_vars['dut3_enable'],
            self.es_vars['dut4_enable'], self.es_vars['dut5_enable'],
            self.es_vars['dut6_enable'], self.es_vars['dut7_enable']
        ]
        
        for i in range(8):
            enable_key = f'dut{i}_enable'
            if self.es_vars.get(enable_key) == "Enable":
                self.dut_ports.append(self.es_vars.get(f'dut{i}'))
                self.dut_names.append(self.es_vars.get(f'dut{i}_name'))
                self.lp_ports.append(self.es_vars.get(f'lp{i}'))
                self.lp_names.append(self.es_vars.get(f'lp{i}_name'))

        if 'Both' in self.es_vars['cable_type']:
            self.cable_plants = [
                ('Cat6a', anil_robot_config.cat6a),
                ('Cat5e', anil_robot_config.cat5e)
            ]
        elif 'Cat6a' in self.es_vars['cable_type']:
            self.cable_plants = [
                ('Cat6a', anil_robot_config.cat6a)
            ]
        else:
            self.cable_plants = [
                ('Cat5e', anil_robot_config.cat5e)
            ]

        #with open(self.es_vars['lengths_file'], 'r') as lengths_file:
            #self.lengths = json.load(lengths_file)
            #self.logger.info(self.lengths)
            
        if "," in self.es_vars['cable_length']:
            string_list = self.es_vars['cable_length'].split(", ")
            int_list = [int(num) for num in string_list]
        else:
            int_list = [int(self.es_vars['cable_length'])]
        
        my_string_length = {}

        for i in range(8):  # 支援 dut0 ~ dut7
            key = f'dut{i}_enable'
            if self.es_vars.get(key) == 'Enable':
                my_string_length[str(i)] = int_list
        
        my_string  = {self.es_vars['cable_type']: my_string_length}
        
        cable_length_file_path  = os.path.join(SAVE_PATH, "temp_cable_length.json")
        
        os.makedirs(os.path.dirname(cable_length_file_path), exist_ok=True)
        
        with open(cable_length_file_path, "w") as file:
            json.dump(my_string, file, indent=4)

        with open(cable_length_file_path, 'r') as file:
            self.lengths = json.load(file)
            #self.logger.info(self.lengths)

        # Configure the logger
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(name)s-%(threadName)s:    %(message)s'
        )

    def main(self):
        speed_map = ['200GBASET-CR4','100GBASET-CR4','100GBASET-CR2','50GBASET-CR2','50GBASET-CR1','25GBASET-CR1']
        """Initial entry point for the robot test."""
        self.list_loop(self.es_vars['cable_type'])
                
        # Test is done, move the heads back to the home positions
        #self.robot.send_home()
        self.logger.info('----------------------------------------')
        self.logger.info('Relaseing all devices ...')
        self.logger.info('----------------------------------------\n')
        if __builtin__._ETHSPY_VARS['dut0_enable'] == 'Enable':
            __builtin__._ETHSPY_VARS['dut0'].close_auto()
            __builtin__._ETHSPY_VARS['lp0'].close_auto()


        if __builtin__._ETHSPY_VARS['dut1_enable'] == 'Enable':
            __builtin__._ETHSPY_VARS['dut1'].close_auto()
            __builtin__._ETHSPY_VARS['lp1'].close_auto()

        if __builtin__._ETHSPY_VARS['dut2_enable'] == 'Enable':
            __builtin__._ETHSPY_VARS['dut2'].close_auto()
            __builtin__._ETHSPY_VARS['lp2'].close_auto()

        if __builtin__._ETHSPY_VARS['dut3_enable'] == 'Enable':
            __builtin__._ETHSPY_VARS['dut3'].close_auto()
            __builtin__._ETHSPY_VARS['lp3'].close_auto()
            
        if __builtin__._ETHSPY_VARS['dut4_enable'] == 'Enable':
            __builtin__._ETHSPY_VARS['dut4'].close_auto()
            __builtin__._ETHSPY_VARS['lp4'].close_auto()
            
        if __builtin__._ETHSPY_VARS['dut5_enable'] == 'Enable':
            __builtin__._ETHSPY_VARS['dut5'].close_auto()
            __builtin__._ETHSPY_VARS['lp5'].close_auto()
            
        if __builtin__._ETHSPY_VARS['dut6_enable'] == 'Enable':
            __builtin__._ETHSPY_VARS['dut6'].close_auto()
            __builtin__._ETHSPY_VARS['lp6'].close_auto()
            
        if __builtin__._ETHSPY_VARS['dut7_enable'] == 'Enable':
            __builtin__._ETHSPY_VARS['dut7'].close_auto()
            __builtin__._ETHSPY_VARS['lp7'].close_auto()

        self.logger.info('----------------------------------------')
        self.logger.info('Test Completed!')
        self.logger.info('----------------------------------------\n')
        csv_file_check = glob.glob(os.path.join(SAVE_PATH,'**','*.csv'),recursive=True)
        if csv_file_check:
            # Do something if there are CSV files
            self.logger.info("CSV files found:")
            for file in csv_file_check:
                self.logger.info(file)
            self.logger.info('There might be no LINK UP during TTL testing! ==> No RX test report!')
        else:
            # Do something else if there are no CSV files
            self.logger.info("No CSV files found. ==> Generate RX test report! \n")
            cable_length_file_path  = os.path.join(SAVE_PATH, "temp_cable_length.json")
            os.remove(cable_length_file_path)
            #call(['py', 'RX_report_autogen.py'])
            if self.speed in speed_map:
                call([sys.executable, 'RX_HSS_report_autogen.py'])
            #elif self.speed == 'HSS_SFP':
            #    call([sys.executable, 'RX_HSS_report_autogen.py'])
            else:
                call([sys.executable, 'RX_report_autogen.py'])

    def list_loop(self, cable_type):
        """Gathers information for each iteration of the test.

        Args:
            position (dict): The desired postions to test.
            cable_type (str): The type of cable being tested, either Cat5e or Cat6a.
        """		
        for dut_port, dut_name, lp_port, lp_name, in zip(
                self.dut_ports, self.dut_names, self.lp_ports, self.lp_names, 
        ):
            dut = self.dev_init.create(dut_port)
            self.logger.info('--------------------')
            self.logger.info('DUT = {}'.format(dut.codename))

            link_partner = self.dev_init.create(lp_port)
            self.logger.info('LP = {}'.format(link_partner.codename))
            self.logger.info('--------------------\n')


            if self.speed in ['2.5GBASET', '5GBASET', '10GBASET']:
                self.es_vars['BER_TARGET'] = 1e-12
                dut.set_base_t_auto_neg([self.speed])
            elif self.speed == '1GBASET':
                self.es_vars['BER_TARGET'] = 1e-10
                dut.set_base_t_auto_neg([self.speed])
                link_partner.set_base_t_auto_neg([self.speed])
                time.sleep(5)


            if self.speed not in ['1GBASET', '2.5GBASET', '5GBASET', '10GBASET']:
                self.es_vars['BER_TARGET'] = 1e-12


            self.prep_to_run(
                dut,
                link_partner,
                dut_name,
                lp_name,
                cable_type
            )

        #count = threading.activeCount()
        count = threading.active_count()
        while count > 1:
            #count = threading.activeCount()
            count = threading.active_count()
            time.sleep(1)

    def prep_to_run(self, dut_prt, link_partner_prt, dut_name, lp_name, cable):
        """Sets up the logger and starts the test.

        Args:
            dut_prt (obj): Object to control to the DUT.
            link_partner_prt (obj): Object to control the link partner.
            dut_name (str): Name of the DUT.
            lp_name (str): Name of the link partner.
            pos (dict): Holds the desired cable lengths to run.
            head_pos (int): The current position of the test head.
            cable (str): The cable type being tested.
        """
        c_name = '{}m_{}'.format(
            self.es_vars['cable_length'], cable
        )

        # Set up the logger
        log_obj = logging.getLogger(
            'DUT-slot{}'.format(dut_prt.slot)
        )
        file_handle = logging.FileHandler(
            os.path.join(
                self.es_vars['OUTPUT_DIR'],
                'DUT_slot{}__LP_slot{}.log'.format(dut_prt.slot, link_partner_prt.slot)
            )
        )
        log_obj.addHandler(file_handle)

        self.es_vars['DUT_NAME'] = dut_name

        test_args = (dut_prt, link_partner_prt, c_name, dut_name, lp_name, log_obj)

        if self.es_vars['parallel'] == 'Enable':
            test_thread = threading.Thread(
                target=self.start_test, args=test_args
            )
            test_thread.start()
        else:
            time.sleep(1)
            self.start_test(*test_args)

    def start_test(self, dut, link_partner, channel, dut_name, lp_name, l_obj):
        """Create an LHC instance with the variables passed in and run the test.

        When the test is complete, a JSON file is created and the scoreboard is written.

        Args:
            dut ():
            link_partner ():
            channel (str): Name of the channel being tested
            dut_name (str):
            lp_name (str):
            position (int):
            l_obj (obj):
        """
        try:
            test = LHC.LHC(
                dut, link_partner, self.link_iterations, self.ber_iterations, channel,
                dut_name, lp_name, self.ttl_delay, self.retry_ttl, l_obj
            )

            results = test.main_test()

            test.write_json_file(results)

        except Exception as err:
            self.logger.info('Error: An error occurred during test execution!\n')
            #self.logger.info(err.message)
            #self.logger.info(traceback.format_exc())
            #self.logger.info('dut_slot = ', dut.slot)
            #self.logger.info('lp_slot = ', link_partner.slot)
            #self.logger.info('channel_name = ', channel)
            #self.logger.info('dut_name = ', dut_name)
            #self.logger.info('lp_name = ', lp_name)
            #self.logger.info('Computing results and writing output files...')

            try:
                test.statistics(test.data)
                test.write_json_file(test.data)
                test.write_csv_file(test.data)
            except NameError:
                self.logger.info('Cannot create output files due to the above error!')

            if str(err) == 'Aborted by user.':
                raise StandardError('Aborted by user.')
            else:
                self.logger.info('\nContinuing to any other ports left to test...\n\n')


if __name__ == '__main__':
    nb = RobotLHCWrapper(logger)
    nb.main()