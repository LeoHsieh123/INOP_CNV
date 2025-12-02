"""
This module is an object-oriented wrapper around ethspy module, provided by EthPy.
It provides the same functionality whether it uses the ethspy.py or the ethpy.cpp module 
"""
import sys
import socket
import ANIL_Robot_LHC_Auto_Config as test_cofig
import ethspy
from time import sleep
default_conn_obj = None
using_python_lib = False
MESSAGE_BOX_CRITICAL = "CRITICAL"
MESSAGE_BOX_WARNING = "WARNING"
MESSAGE_BOX_INFO = "INFO"

class EthSpyError(Exception):
    """
    Custom exception class to raise Intel Ethernet Inspector specific exceptions.

    Attributes:
        message (string): Custom error message
    """
    def __init__(self, message):
        """
        Initializes the EthSpyError object
        
        Args:
            message (string): Custom error message
        """
        
        message = 'EthSpyError: ' + message
        super(EthSpyError, self).__init__(message)
        self.message = message

    def get_message(self):
        """
        Returns the error message
        """
        return self.message

class Port(object):
    """
    This class implements Port as a device type.

    Attributes:
        host_name (string): host name as specified in Intel Ethernet Inspector's device tree
        slot_number (string): slot number for the selected host name in Intel Ethernet Inspector's device tree
    """

    def __init__(self, host_name, slot_number, logger,logger2):
        """
        Constructor for Port instance.
        
        Args:
            host_name (string): host name as specified in Intel Ethernet Inspector's device tree
            slot_number (string): slot number for the selected host_name, 
                                    as specified in Intel Ethernet Inspector's device tree
        """
        if False == slot_number.isdigit():
            raise EthSpyError('slot_number must be a digit')

        self.logger = logger
        self.logger2 = logger2
        self.host_name = str(host_name)
        self.slot_number = str(slot_number)
        self.port_id = None
        
        if using_python_lib:
            self.conn = None
            global default_conn_obj
            self.conn = default_conn_obj[host_name]

    def open_auto(self):
        remote_ip_port =self.host_name.split(":")
        ip = remote_ip_port[0]
        ip_port = int(remote_ip_port[1])
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        addr= (ip,ip_port)
        self.conn.connect(addr)
        self.logger.info("Successfully connected to EthAgent, IP:Port = {}".format(self.host_name))
        self.port_id = ethspy.open_port(self.conn, self.slot_number,self.logger,self.logger2)
        self.conn.close()

    def close_auto(self):
        remote_ip_port =self.host_name.split(":")
        ip = remote_ip_port[0]
        ip_port = int(remote_ip_port[1])
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        addr= (ip,ip_port)
        self.conn.connect(addr)
        self.logger.info("Successfully connected to EthAgent, IP:Port = {}".format(self.host_name))
        self.port_id = ethspy.del_port(self.conn, self.slot_number,self.logger,self.logger2)
        self.conn.close()

    def open(self):
        """
        Opens the connection to Intel Ethernet Inspector's unique host_name:port_number device
        """
        if using_python_lib:
            ethspy.open_port(self.conn, self.slot_number)
        else:
            self.port_id = ethspy.open_port(self.host_name, self.slot_number)
            if not self.port_id:
                raise EthSpyError('port open failed for host: ' + self.host_name +
                                  ' and slot: ' + self.slot_number)

    def execute(self, command):
        """
        Executes the command on already opened port. The command must start with case-insensitive
        'hostCommand' word.

        Args:
            command (string): command to be executed on the port, must start with hostCommand
        """
        remote_ip_port =self.host_name.split(":")
        ip = remote_ip_port[0]
        ip_port = int(remote_ip_port[1])
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        addr= (ip,ip_port)
        self.conn.connect(addr)
        if using_python_lib:
            if None == self.conn:
                raise EthSpyError('port is not open, please open it again using Port.open()')
            
            if command == 'GetSlotNumber':
                return self.slot_number
            
            cmds = command.split(" ")
            if command[:len('hostCommand')].lower() == 'hostcommand':
                if len(cmds) < 2:
                    raise Exception("Error: hostCommand needs at least one parameter")
                lstr_temp_list = ["hostCommand"]
                cmds = cmds[1:]
                cmds[0] = cmds[0] + ':' + str(self.slot_number)
                lstr_temp_list.append(' '.join(cmds))
                cmds = lstr_temp_list
            else:
                 if len(cmds) > 1:
                     lstr_temp_list = [cmds[0]]
                     cmds = cmds[1:]
                     lstr_temp_list.append(' '.join(cmds))
                     cmds = lstr_temp_list
                 cmds.insert(1, str(self.slot_number))
            
            cmds[1] = cmds[1] + '\n'
            return ethspy.exec_port(self.conn, cmds)
        else:
            if None == self.port_id:
                raise EthSpyError('port is not open, please open it again using Port.open()')

            cmds = command.split(" ")
            if command[:len('hostCommand')].lower() == 'hostcommand':
                if len(cmds) < 2:
                    raise Exception("Error: hostCommand needs at least one parameter")
                lstr_temp_list = ["hostCommand"]
                cmds = cmds[1:]
                cmds[0] = cmds[0] + ':' + str(self.slot_number)
                lstr_temp_list.append(' '.join(cmds))
                cmds = lstr_temp_list
            else:
                 if len(cmds) > 1:
                     lstr_temp_list = [cmds[0]]
                     cmds = cmds[1:]
                     lstr_temp_list.append(' '.join(cmds))
                     cmds = lstr_temp_list
                 cmds.insert(1, str(self.slot_number))
            
            cmds[1] = cmds[1] + '\n'
            if test_cofig.EthAgent_command == 'Enable':
                #self.logger.info("IP:Port = {}:{}, EthAgent command = {}".format(ip,ip_port,cmds[1]))
                self.logger2.info("IP:Port = {}:{}, EthAgent command = {}".format(ip,ip_port,cmds[1]))
            return ethspy.exec_port(self.conn, cmds[1])

    def close(self):
        """
        Closes the port if open
        """
        if using_python_lib:
            if self.conn is not None:
                ethspy.close_port(self.conn)
        else:
            if self.port_id is not None:
                ethspy.close_port(self.port_id)

def message_box(box_type, title, message):
    if box_type not in (MESSAGE_BOX_CRITICAL, MESSAGE_BOX_WARNING, MESSAGE_BOX_INFO):
        raise EthSpyError('Invalid message box type. valid types are - %s, %s, %s.' % 
                            MESSAGE_BOX_CRITICAL, MESSAGE_BOX_WARNING, MESSAGE_BOX_INFO)
    return ethspy.message_box(box_type, title, message)

def get_version():
    return ethspy.get_version()