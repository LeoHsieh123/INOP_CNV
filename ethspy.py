import socket
import select
import time
import ANIL_Robot_LHC_Auto_Config as test_cofig

def check_end_msg(msg):
    if msg[-len('OK\r\n'):] == 'OK\r\n':
        return True
    else:
        return False
 
def open_port(conn, slot,logger,logger2):
    conn.sendall('ADD {}\n'.format(slot).encode())
    if test_cofig.EthAgent_command == 'Enable':
        #logger.info("EthAgent command = ADD {}".format(slot))
        logger2.info("EthAgent command = ADD {}".format(slot))
    logger.info("Initialize Slot {} ...\n".format(slot))
    msg = ''
    while check_end_msg(msg) == False:
        msg += conn.recv(65536).decode()
    
    
    if "warning" in msg.lower():
        #logger.info(msg)
        logger2.info(msg)
    elif 'error' in msg.lower():
        raise Exception(msg)
    return conn

def del_port(conn, slot,logger,logger2):
    conn.sendall('DEL {}\n'.format(slot).encode())
    if test_cofig.EthAgent_command == 'Enable':
        #logger.info("EthAgent command = DEL {}".format(slot))
        logger2.info("EthAgent command = DEL {}".format(slot))
    logger.info("Release Slot {} ...\n".format(slot))
    msg = ''
    while check_end_msg(msg) == False:
        msg += conn.recv(65536).decode()
    
    
    if "warning" in msg.lower():
        #logger.info(msg)
        logger2.info(msg)
    elif 'error' in msg.lower():
        raise Exception(msg)
    return conn
    
def close_port(conn):
    pass
    
def exec_port(conn, cmd):
    conn.sendall(cmd.encode())
    msg = ''
    while check_end_msg(msg) == False:
        msg += conn.recv(65536).decode()
        #logger.info('msg:', msg)
        #logger2.info('msg:', msg)
    msg = msg[:-5]
    return msg
  
def get_version():
    return "standalone"
