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
    def __init__(self, Q : G1, m0 : str, m1 : str) -> None:
        self.m = [m0, m1]
        self.Q = Q

    def get_A(self):
        self.a = Fr.rnd()
        self.A = self.Q * self.a
        return self.A

    def get_encrypted(self, B):
        k0 = Fr.setHashOf(f'{B*self.a}'.encode())
        k1 = Fr.setHashOf(f'{(B - self.A)*self.a}'.encode())

        e0 = xor_strings(self.m[0], k0.getStr().decode())
        e1 = xor_strings(self.m[1], k1.getStr().decode())

        return [e0, e1]




class Receiver:
    def __init__(self, Q : G1, c : int) -> None:
        self.c = c
        self.Q = Q

    def get_B(self, A : G1):
        b = Fr.rnd()
        self.kr = Fr.setHashOf(f'{A*b}'.encode())

        if self.c == 0:
            B = self.Q * b
        elif self.c == 1:
            B = A + (self.Q * b)
        else:
            raise Exception("C not in range")

        return B

    def decrypt(self, e : list[str]):
        ec = e[self.c]

        m = xor_strings(self.kr.getStr().decode(), ec)
        return remove_trailing_zeros(m)



REQ_GET_A  = 'get_a'
SEND_B = 'B.json'


import json
def read_list_json(json_str, json_name):
    # logging.info(f'{json_str=}')
    r_json = json.loads(json_str)
    return [mcljson.mcl_from_str(Ri, G1) for Ri in r_json[json_name]]

def write_list_json(filename : str, json_name, number_list):
    json_dict = {
        json_name : number_list
    }
    mcljson.write_json_mcl(filename, json_dict)







run_server = (sys.argv[1] == "server")
run_client = (sys.argv[1] == "client")
if sys.argv[1] == "both":
    run_server = True
    run_client = True

if run_server:
    PORT = 8000
    server_url = f'http://localhost:{PORT}'
else:
    assert len(sys.argv) == 3
    server_url = sys.argv[2]



Q = G1().hashAndMapTo(b'test')
m = [f"message {i}" for i in range(2)]



if run_server:
    def sender_process_function(file_data : bytes, filename : str, message : str):
        logging.info(f'sender_process_function({file_data=}, {filename=}, {message=})')
        if message is not None:
            if message == REQ_GET_A:
                processed_file_path = f'{SERVER_PATH}/R.json'
                A = sender.get_A()
                write_list_json(processed_file_path, "A", [A])
                return processed_file_path
            raise Exception(f'{message=}')
        else:
            if filename == SEND_B:
                B = read_list_json(file_data.decode(), "B")[0]
                e = sender.get_encrypted(B)
                processed_file_path = f'{SERVER_PATH}/e.json'
                write_list_json(processed_file_path, 'e', e)
                return processed_file_path
            raise Exception(f'{filename=}')

    def run_server():
        global sender
        sender = Sender(Q, *m)
        server.run_server(sender_process_function, port=PORT)


    server_thread = threading.Thread(target=run_server)
    server_thread.start()
    time.sleep(3)


if run_client:
    i = 1
    receiver = Receiver(Q, i)

    # A = sender.get_A()
    response_json = client.send_message_to_server(REQ_GET_A, server_url)
    print(f'{response_json=}')
    A = read_list_json(response_json, "A")[0]

    B = receiver.get_B(A)

    # e = sender.get_encrypted(B)
    processed_file_path = f'{CLIENT_PATH}/{SEND_B}'
    write_list_json(processed_file_path, "B", [B])
    response_json = client.send_file_to_server(processed_file_path, server_url)
    e = read_list_json(response_json, "e")

    mc = receiver.decrypt(e)

    # check for success
    print(f'{m[i].encode()}; {mc.encode()};')
    print(f'{m[i]=}; {mc=};')

    success = m[i] == mc
    if success:
        print('Success')
    else:
        print('Failed')




