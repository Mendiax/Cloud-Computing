from mcl import *

import time
import threading
from utilities import *
import logging
import sys


import server
import client
import mcljson



CLIENT_PATH = 'client'
SERVER_PATH = 'server'


# Configure logging for the client
logging.basicConfig(level=logging.INFO, filename='client.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')


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
        assert self.i < len(R), f"{self.i}, {R}"
        W = R[self.i] * alpha

        self.ki = Q*alpha
        return W

    def decrypt(self, c : list[str]):
        return decrypt(c[self.i], self.ki)


REQ_GET_R  = 'get_r'
REQ_W_FILE = 'W.json'
REQ_E_FILE = 'e.json'


import json
def read_list_json(json_str, json_name):
    # logging.info(f'{json_str=}')
    r_json = json.loads(json_str)
    val = r_json[json_name]
    # print(json_name)
    # print(type(val))
    # print(val)
    if isinstance(val, list):
        # print('list')
        return [mcljson.mcl_from_str(Ri, G1) for Ri in val]
    else:
        return mcljson.mcl_from_str(val, G1)


def write_list_json(filename : str, json_name, number_list):
    json_dict = {
        json_name : number_list
    }
    mcljson.write_json_mcl(filename, json_dict)





# run_server = False
# run_client = True
# server_url = 'http://192.168.80.226:8000'
# time.sleep(10)

run_server = (sys.argv[1] == "server")
run_client = (sys.argv[1] == "client")
if sys.argv[1] == "both":
    run_server = True
    run_client = True

if run_server:
    PORT = 56000
    server_url = f'http://localhost:{PORT}'
else:
    # assert len(sys.argv) == 3
    server_url = 'http://192.168.80.226:56000'

print(server_url)

Q = G1().hashAndMapTo(b'test')
m = [f"message {i}" for i in range(10)]



if run_server:
    def sender_process_function(file_data : bytes, filename : str, message : str):
        logging.info(f'sender_process_function({file_data=}, {filename=}, {message=})')
        if message is not None:
            if message == REQ_GET_R:
                processed_file_path = f'{SERVER_PATH}/R.json'
                R = sender.get_R()
                write_list_json(processed_file_path, "R", R)
                return processed_file_path
            raise Exception(f'{message=}')
        else:
            if filename == REQ_W_FILE:
                e = sender.get_encrypted(W)
                processed_file_path = f'{SERVER_PATH}/{REQ_E_FILE}'
                write_list_json(processed_file_path, 'e', e)
                return processed_file_path
            raise Exception(f'{filename=}')

    def run_server():
        global sender
        sender = Sender(Q, m)
        server.run_server(sender_process_function, port=PORT)


    server_thread = threading.Thread(target=run_server)
    server_thread.start()
    time.sleep(2)


if run_client:
    i = 4
    receiver = Receiver(Q, i)

    response_json = client.send_message_to_server(REQ_GET_R, server_url)
    # print(f'{response_json=}')
    R = read_list_json(response_json, "R")


    W = receiver.get_W(R)
    processed_file_path = f'{CLIENT_PATH}/{REQ_W_FILE}'
    write_list_json(processed_file_path, "W", W)
    response_json = client.send_file_to_server(processed_file_path, server_url)
    e = json.loads(response_json)['e']
    mc = receiver.decrypt(e)


    # check for success
    print(f'received: {mc.encode()}')
    # print(f'{m[i].encode()}; {mc.encode()};')
    # print(f'{m[i]=}; {mc=};')

    # success = m[i] == mc
    # if success:
    #     print('Success')
    # else:
    #     print('Failed')




