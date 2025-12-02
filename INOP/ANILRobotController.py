import sys
import serial
import time
import re
import socket


# TODO: Threading

class RobotServer:
    def __init__(self, robot, port, type, logger):
        self.logger = logger
        self.robot = robot
        self.type = type
        self.run_server(port)

    def run_server(self, port):
        self.host = '0.0.0.0'
        self.port = int(port)
        self.s = socket.socket()
        self.s.bind((self.host, self.port))
        self.s.listen(1)
        self.conn, self.addr = self.s.accept()
        self.s.settimeout(0)
        self.logger.info('connection established')
        self.conn.send('True,None\n'.encode())

        while True:
            try:
                self.dat = self.conn.recv(1024).decode()
                if len(self.dat) > 0:
                    if self.dat == 'quit':
                        if self.type == 'Virtual':
                            self.robot.quit_robot()
                            self.conn.send('True, None\n'.encode())
                            self.s.close()
                            return 0
                        else:
                            self.conn.send('True, None\n'.encode())
                            self.s.close()
                            return 0
                    else:
                        self.response = self.robot.command_handler(self.dat) + '\n'
                        self.conn.send(self.response.encode())
                else:
                    raise Exception('Socket closed')
            except Exception as e:
                self.logger.info(e)
                try:
                    self.s.setblocking(1)
                    self.s.listen(1)
                    self.conn, self.addr = self.s.accept()
                    self.s.setblocking(0)
                    self.logger.info('connection established')
                    self.conn.send('True, None\n'.encode())
                except:
                    pass
                    # put error handling in here


class ANILRobot(object):
    """Class used for interfacing with Haifa robot over serial interface."""

    def __init__(self, ser,logger):
        """Core constructor builds robot object, sets target device into remote mode, queries the current status of the robot
        
        Args:
            ser (str): Which COM port to communicate with the robot over, e.g. COM3
        """
        self.logger = logger
        self.front_head_position = ''
        self.rear_head_position = ''
        
        self.session = serial.Serial(ser, 9600, timeout=60, parity=serial.PARITY_NONE, bytesize=8, stopbits=1)
        self.response_log = []
        self.shared_command_list()
        self.set_remote()
        #self.send_home()
        #self.update_current_status()

    def send_home(self):
        self.logger.info('----------------------------------------')
        self.logger.info('ROBOT: Sending front head to the home position... please wait.')
        self.logger.info('----------------------------------------')
        self.send_command(self.home_front)
        self.logger.info('----------------------------------------')
        self.logger.info('ROBOT: Sending rear head to the home position... please wait.')
        self.logger.info('----------------------------------------')
        self.send_command(self.home_rear)

    def quit_robot(self):
        self.session.write('Exit0'.encode())
        self.session.close()

        return 'Session ended.'

    def set_remote(self):
        '''
            Sets the robot into remote access mode
            Parameters: None
        '''
        return self.send_command(self.remote_mode)

    def shared_command_list(self):
        """Creates lists for checking valid responses."""

        # Commands that are shared, regardless of which robot configuration is present
        self.remote_mode = '281F3'  # Convert the robot to remote control mode
        self.home_front = '230F3'
        self.status_head_front = '274F3'  # Expected Responses are 275F3 for IN 276F3 for OUT
        self.status_pos_front = '272F3'  # Expected responses are the command codes to send the device to a given location
        self.status_head_rear = '274R3'
        self.status_pos_rear = '272R3'
        self.home_rear = '230R3'

        self.error_conditions = {
            '279F3': 'Front Calibration Failure',
            '279R3': 'Rear Calibration Failure',
            '297F3': 'Front Door Open',
            '297R3': 'Rear Door Open',
            '294F3': 'Front Door Closed',
            '294R3': 'Rear Door Closed',
            '298F3': 'Front Emergency Switch Pressed',
            '298R3': 'Rear Emergency Switch Pressed',
            '299F3': 'Front Emergency Switch Released',
            '299R3': 'Rear Emergency Switch Released',
            '296F3': 'Front Motor Alarm',
            '296R3': 'Rear Motor Alarm',
            '292F3': 'Front Insert Failure',
            '292R3': 'Rear Insert Failure'
            #'295F3': 'Illegal Data Front',
            #'295R3': 'Illegal Data Rear'
        }

        self.front_arm_positions = [
            '200F3', '201F3', '202F3', '203F3', '204F3', '205F3', '206F3',
            '207F3', '208F3', '209F3', '210F3', '211F3', '212F3',
            '213F3', '214F3', '215F3', '216F3', '217F3', '218F3', '219F3',
            '220F3', '230F3', '295F3'
        ]

        self.rear_arm_positions = [
            '200R3', '201R3', '202R3', '203R3', '204R3', '205R3', '206R3',
            '207R3', '208R3', '209R3', '210R3', '211R3', '212R3',
            '213R3', '214R3', '215R3', '216R3', '217R3', '218R3', '219R3',
            '220R3', '230R3', '295R3'
        ]

        self.customer_positions = {
            ('201F3', '201R3'): '00',
            ('205F3', '202R3'): '01',
            ('205F3', '203R3'): '02',
            ('205F3', '204R3'): '03',
            ('205F3', '205R3'): '04',
            ('205F3', '206R3'): '05',
            ('205F3', '207R3'): '06',
            ('205F3', '208R3'): '07',
            ('205F3', '209R3'): '08',
			('205F3', '210R3'): '09',
            ('205F3', '211R3'): '10',
            ('205F3', '212R3'): '11',
            ('205F3', '213R3'): '12',
            ('214F3', '214R3'): '13',
            ('214F3', '215R3'): '14',
            ('214F3', '216R3'): '15',
            ('214F3', '217R3'): '16',
            ('214F3', '218R3'): '17',
            ('214F3', '219R3'): '18',
            ('214F3', '220R3'): '19',
            ('209F3', '201R3'): '20',
            ('209F3', '202R3'): '21',
            ('209F3', '203R3'): '22',
            ('209F3', '204R3'): '23',
            ('209F3', '205R3'): '24',
            ('209F3', '206R3'): '25',
            ('209F3', '207R3'): '26',
            ('209F3', '208R3'): '27',
            ('209F3', '209R3'): '28',
            ('230F3', '230R3'): 'Home'
        }

        self.valid_locations = {
            '30': ('230F3', '230R3'),
            '00': ('201F3', '201R3'),
			'01': ('205F3', '202R3'),
            '02': ('205F3', '203R3'),
            '03': ('205F3', '204R3'),
            '04': ('205F3', '205R3'),
            '05': ('205F3', '206R3'),
            '06': ('205F3', '207R3'),
            '07': ('205F3', '208R3'),
            '08': ('205F3', '209R3'),
			'09': ('205F3', '210R3'),
            '10': ('205F3', '211R3'),
            '11': ('205F3', '212R3'),			
            '12': ('205F3', '213R3'),
            '13': ('214F3', '214R3'),
            '14': ('214F3', '215R3'),
            '15': ('214F3', '216R3'),
            '16': ('214F3', '217R3'),
            '17': ('214F3', '218R3'),
            '18': ('214F3', '219R3'),
            '19': ('214F3', '220R3'),
            '20': ('209F3', '201R3'),
            '21': ('209F3', '202R3'),
            '22': ('209F3', '203R3'),
            '23': ('209F3', '204R3'),
            '24': ('209F3', '205R3'),
            '25': ('209F3', '206R3'),
            '26': ('209F3', '207R3'),
            '27': ('209F3', '208R3'),
            '28': ('209F3', '209R3')
        }

    def send_command(self, command):
        """Writes to the serial interface the command string parameter.
        
        Args:
            command (str): Command to send to the robot, e.g. '230F3'

        Returns:

        """
        if self.detect_valid_command(command):
            self.session.flushInput()
            cmd = command.encode()

            if command in self.valid_locations:
                self.logger.info('COMMAND = ', command)
                self.logger.info('self.front_head_position = ', self.front_head_position)
                self.logger.info('self.rear_head_position  = ', self.rear_head_position)
                if command != self.front_head_position or command != self.rear_head_position:
                    self.session.write(cmd)
                    response = self.read_response('move', cmd)
                    if 'F' in command:
                        self.front_head_position = command
                    elif 'R' in command:
                        self.rear_head_position = command
                else:
                    response = 'No action taken'
            elif command in self.front_arm_positions:
                self.logger.info('ROBOT: Moving front head...')
                self.logger.info('COMMAND = {}'.format(command))
                self.logger.info('CURRENT Front Head Position = {}'.format(self.front_head_position))
                
                if command != self.front_head_position:
                    self.session.write(cmd)
                    response = self.read_response('move', cmd)
                    self.front_head_position = command
                else:
                    response = 'No action taken'
                self.logger.info('NEW Front Head Position = {}\n'.format(self.front_head_position))
            elif command in self.rear_arm_positions:
                self.logger.info('ROBOT: Moving rear head...')
                self.logger.info('COMMAND = {}'.format(command))
                self.logger.info('CURRENT Rear Head Position = {}'.format(self.rear_head_position))
                
                if command != self.front_head_position:
                    self.session.write(cmd)
                    response = self.read_response('move', cmd)
                    self.rear_head_position = command
                else:
                    response = 'No action taken'
                self.logger.info('NEW Rear Head Position = {}\n\n'.format(self.rear_head_position))
            else:
                self.session.write(cmd)
                response = self.read_response('query', cmd)
                self.logger.info('ROBOT RESPONSE:{}'.format(response))
        else:
            response = self.error_handler('Invalid Command')

        return response
    
    def update_current_status(self):
        """Queries the robot and updates state variables tracking its current status, assigns them as properties of the robot object
        
        Returns three strings:  Configuration location, Front Head Status, Rear Head Status
        
        STATUS:  Looks right
        """
        head_status = {'75': 'In', '76': 'Out'}
        cmd_type = 'query'
        current_front_head_status = self.send_command(self.status_head_front)
        current_front_head_status = current_front_head_status[len(current_front_head_status) - 5:len(current_front_head_status)]
        current_rear_position = self.send_command(self.status_pos_rear)
        current_rear_position = current_rear_position[len(current_rear_position) - 5:len(current_rear_position)]
        current_rear_head_status = self.send_command(self.status_head_rear)
        current_rear_head_status = current_rear_head_status[len(current_rear_head_status) - 5:len(current_rear_head_status)]
        current_front_position = self.send_command(self.status_pos_front)
        current_front_position = current_front_position[len(current_front_position) - 5:len(current_front_position)]
        loops = 0
        while current_front_position[3] == 'R':
            current_front_position = self.send_command(self.status_pos_front)
            current_front_position = current_front_position[len(current_front_position) - 5:len(current_front_position)]
            loops += 1
            if loops > 20:
                return self.error_handler('Front position failed to respond')
            else:
                continue
        front_head_status = head_status[current_front_head_status[1:3]]
        rear_head_status = head_status[current_rear_head_status[1:3]]
        position = self.customer_positions[(current_front_position, current_rear_position)]

        return position, front_head_status, rear_head_status

    def command_handler(self, cmd):
        """Expected commands(command list):
                Movement commands:
                    CAT6a primary: (00-08)
                    CAT5e: (10-19)
                    CAT6a secondary: (20-28)
                    Home: 30
                Movement commands are int type
                Status commands:
                    status(74) -- Current Head Status
                    position(72) -- Current Head location
                Status commands take tuple type(front_cmd, rear_cmd)
            
        STATUS:  Looks right
        """
        valid_queries = ['position', 'status']
        received_cmd = cmd

        # Check Type to deteremine what to do
        if received_cmd in valid_queries:
            position, front_head_status, rear_head_status = self.update_current_status()

            if received_cmd == 'position':
                output = 'True, {}'.format(position)
            elif received_cmd == 'status':
                output = 'True, {}, {}'.format(
                    front_head_status, rear_head_status
                )
            else:
                output = self.error_handler('Invalid Query')

        elif received_cmd in self.valid_locations:
            # Movement command received
            output = self.move_robot(received_cmd)

        elif received_cmd == 'quit':
            output = self.quit_robot()

        else:
            output = self.error_handler('Invalid Command Type')

        return output

    def move_robot(self, pos):
        """Takes received position command, translates it to front/rear positions.
        
        Sends commands to move front/rear arms, returns True if complete, False if error.
        
        STATUS:  Looks right
        
        Args:
            pos (): 

        Returns:

        """
        # CAT6A primary segments (Lead Head(n), (n-1), (n-2), (n-3))

        move_response = ''
        if pos in self.valid_locations:
            for x in range(2):
                move_response = move_response + self.send_command(self.valid_locations[pos][x]) + ','
            move_response = move_response[0:len(move_response) - 1]
            return move_response
        else:
            return self.error_handler('Invalid Position')

    def error_handler(self, err):
        """Centralized function to handle and return errors.
        
        This could be done way better
        """
        err_status = {
            'Invalid Command Type': '101',
            'Status Error': '102',
            'Invalid Position': '103',
            'Read Timeout': '104',
            'Unhandled Read Error': '105',
            'Hardware Error': '106',
            'Command Type Not Recognized': '107',
            'Move Error': '108',
            'Query Timeout': '109',
            'Invalid Query': '110',
            'Invalid Command': '111',
            'Front position failed to respond': '112'

        }

        return 'False, {}'.format(err_status[err])

    def detect_valid_command(self, command):
        valid_start = command[0]
        valid_stop = command[-1]
        valid_length = len(command)
        valid_command_code_list = ['30', '00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12',
                                   '13', '14', '15', '16', '17', '18', '19', '20', '79', '74', '72', '81']
        # These commands will result in the same command being sent back twice.  The control software should be looking for the error codes in either the first 5 or second 5 bytes returned by the robot
        # Depending on the error code, it may be the first response or the second response from the robot
        if valid_start == '2' and valid_stop == '3' and valid_length == 5 and (
            command[1:3] in valid_command_code_list) and (command[3] == 'F' or command[3] == 'R'):
            return True
        else:
            return False
            
    def read_response(self, cmd_type, cmd_sent):
        """Reads the robot responses to commands sent.
        
        Args:
            cmd_type (str): 
            cmd_sent (str): 

        Returns:
            str: Response from the robot
        """
        # Need to include some safety around the fact that the robot erroneously
        # responds with rear position
        read_error_timeout = 35.0  # No movement of the robot should take more than 35 seconds
        query_timeout = 2.0  # Queries should respond quickly, small delay to allow serial interface delay
        move_timeout = 30.0  # Check time for response from move command
        raw_buffer_data = ''
        received_responses = []
        start_timer = time.time()

        while True:
            timeout_expired = (time.time() - start_timer) > read_error_timeout
            # print-timeout_expired
            query_timeout_expired = (time.time() - start_timer) > query_timeout
            if timeout_expired:
                return self.error_handler('Read Timeout')
            else:
                if self.session.inWaiting() > 0:
                    raw_buffer_data = raw_buffer_data + self.session.read(self.session.inWaiting()).decode()
                else:
                    time.sleep(0.5)
            received_responses = re.findall('2...3', raw_buffer_data)
            if (cmd_type == 'query') and ((time.time() - start_timer) > query_timeout) and (len(received_responses) >= 2):
                self.response_log.append(received_responses)
                no_error_condition = self.check_for_robot_errors(received_responses)
                if no_error_condition:
                    return 'True, {}'.format(received_responses[-1])
                else:
                    return self.error_handler('Robot Error Detected')
            elif cmd_type == 'move' and ((time.time() - start_timer) > move_timeout) and (len(received_responses) >= 2):
                if received_responses[-1] == cmd_sent:
                    self.response_log.append(received_responses)
                    self.check_for_robot_errors(received_responses)
                    no_error_condition = self.check_for_robot_errors(received_responses)
                    if no_error_condition:
                        return 'True, {}'.format(received_responses[-1])
                    else:
                        return self.error_handler('Robot Error Detected')
                else:
                    return self.error_handler('Move Error')
            else:
                continue

    def check_for_robot_errors(self, rec_responses):
        """Function that looks to see if the robot has thrown any errors."""
        for item in rec_responses:
            if item in self.error_conditions:
                return False
            else:
                continue
        return True


def main(argv):
    """This is called with 3 parameters
        Parameter 1: COM port of the robot, e.g. COM6
        Parameter 2: Port of the TCP/IP socket, e.g. 8087
        Parameter 3: Virtual or Physical robot, e.g. 'Virtual'
    """
    # com = 'COM6'
    # port = 8087
    # typ = 'Physical'
    # r = HaifaRobot(com)
    # server = RobotServer(r, port, typ)
    r = ANILRobot(argv[0],logger)
    server = RobotServer(r, argv[1], argv[2],logger)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
