# Standard library imports
import sys
import socket
import logging
import os
import threading
import time
import traceback
import logging
from pathlib import Path

# Local project imports
import ANILRobot_Head_Control
import anil_robot_config


class RobotLHCWrapper():
    def __init__(self,logger):
        self.logger = logger
        self.robot = ANILRobot_Head_Control.ANILRobot('COM3',logger)
	
    def main(self):
        robot_moving =input("\nPlease press <MOVE TO> button after new position selected.\n")
        
        if robot_moving == '1':
            #Move to Home
            self.robot.send_home()
            
            self.logger.info("Robot: Moving Done!")
            
        elif robot_moving == '2':
            #Move Frond Head
            self.robot.send_command('205F3')

            #Move Rear Head
            self.robot.send_command('205R3')
            
            self.logger.info("Robot: Moving Done!")
        
        elif robot_moving == '3':
            #Move Frond Head
            self.robot.send_command('205F3')

            #Move Rear Head
            self.robot.send_command('209R3')
            
            self.logger.info("Robot: Moving Done!")
            
        elif robot_moving == '4':
            #Move Frond Head
            self.robot.send_command('205F3')

            #Move Rear Head
            self.robot.send_command('213R3')
            
            self.logger.info("Robot: Moving Done!")
            
        elif robot_moving == '5':
            #Move Frond Head
            self.robot.send_command('214F3')

            #Move Rear Head
            self.robot.send_command('217R3')
            
            self.logger.info("Robot: Moving Done!")

        else:
            self.logger.info("Wrong input!  No action!")
            pass

if __name__ == '__main__':
    file_path = "C:\BER\head_control.log"
    my_file = Path(file_path)
    if my_file.is_file():
        os.remove(file_path)
    
    logging.basicConfig(
        level=logging.DEBUG,  # Set the logging level
        format='%(asctime)s - %(message)s',  # Set the format for log messages
        handlers=[
            #logging.FileHandler("C:\BER\head_control.log"),  # Log to a file
            logging.StreamHandler()  # Also log to console
        ]
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Please wait for Robot connection...")
    nb = RobotLHCWrapper(logger)
    nb.main()