import time
from mcl import *

from utilities import *
import logging

# # Configure logging for the client
# logging.basicConfig(level=logging.INFO, filename='client.log', filemode='a',
#                     format='%(asctime)s - %(levelname)s - %(message)s')
# ANSI escape sequences for colors in the terminal
class CustomFormatter(logging.Formatter):
    """Logging Formatter to add colors and count warning / errors"""

    green = "\x1b[32;20m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(levelname)s - %(message)s"

    FORMATS = {
        logging.INFO: green + format + reset,
        logging.ERROR: format,
        logging.WARNING: format,
        logging.DEBUG: format,
        logging.CRITICAL: format
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)

# Get the root logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# Create formatter and add it to the handlers
ch.setFormatter(CustomFormatter())

# Add the handlers to the logger
logger.addHandler(ch)


class Sender:
    def __init__(self, Q : G1, m : list[str]) -> None:

        self.m = m
        self.n = len(m)
        self.Q = Q
        self.r = [Fr.rnd() for _ in range(self.n)]
        self.R = [Q * r for r in self.r]

    def get_R(self):
        return self.R

    def get_encrypted(self, W):
        _1 = Fr()
        _1.setInt(1)
        k = [W * (_1/r) for r in self.r]
        c = [encrypt(m,k) for m,k in zip(self.m, k)]

        return c





class Receiver:
    def __init__(self, Q : G1, i : int) -> None:
        self.i = i
        self.Q = Q

    def get_W(self, R : list[G1]):
        alpha = Fr.rnd()
        assert self.i < len(R)
        W = R[self.i] * alpha

        self.ki = Q*alpha
        return W

    def decrypt(self, c : list[str]):
        return decrypt(c[self.i], self.ki)


Q = G1().hashAndMapTo(b'test')

m = [f"message {i}" for i in range(100)]
i = 15

REQ_GET_R = 'get_r'
REQ_W_FILE = 'W.json'
REQ_E_FILE = 'e.json'


def write_G1_list(filename : str, json_name, number_list):
    json_dict = {
        json_name : number_list
    }
    mcljson.write_json_mcl(filename, json_dict)


sender = Sender(Q, m)
receiver = Receiver(Q, i)
import mcljson
def sender_process_function(file_data : bytes, filename : str, message : str):
    logging.info(f'sender_process_function({file_data=}, {filename=}, {message=})')
    if message is not None:
        if message == REQ_GET_R:
            processed_file_path = 'R.json'
            R = sender.get_R()
            write_G1_list(processed_file_path, "R", R)

            return processed_file_path
        raise Exception(f'{message=}')
    else:
        if filename == REQ_W_FILE:
            e = sender.get_encrypted(W)
            processed_file_path = REQ_E_FILE
            write_G1_list(processed_file_path, 'e', e)
            return processed_file_path
        raise Exception(f'{filename=}')




import json
def read_R(json_str):
    # logging.info(f'{json_str=}')
    r_json = json.loads(json_str)
    return [mcljson.mcl_from_str(Ri, G1) for Ri in r_json['R']]

import server
import client

import threading

PORT = 8000
server_url = f'http://localhost:{PORT}'
def run_server():
    server.run_server(sender_process_function, port=PORT)
server_thread = threading.Thread(target=run_server)
server_thread.start()

time.sleep(2)

response_json = client.send_message_to_server(REQ_GET_R, server_url)
# logging.info(f'{response_json=}')
R = read_R(response_json)


W = receiver.get_W(R)
processed_file_path = REQ_W_FILE
write_G1_list(processed_file_path, "W", W)
# send W

response_json = client.send_file_to_server(processed_file_path, server_url)
e = json.loads(response_json)['e']

mc = receiver.decrypt(e)

print(f'{m[i].encode()}; {mc.encode()};')
print(f'{m[i]=}; {mc=};')

success = m[i] == mc
if success:
    print('Success')
else:
    print('Failed')




