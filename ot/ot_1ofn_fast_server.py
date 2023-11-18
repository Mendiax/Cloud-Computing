import secrets
from tkinter.tix import Tree
from mcl import *

import math
import time
import threading

import mcl
from utilities import *
import logging
import sys
import hashlib
import json


import server
import client
import mcljson



CLIENT_PATH = 'client'
SERVER_PATH = 'server'



M_SIZE = 2048 # bytes
K_SIZE = 128 # bytes
K_NUM = math.ceil((M_SIZE) / K_SIZE)
set_xor_max_len(M_SIZE)




# OT 1 of 2
REQ_GET_A  = 'get_r'
A_LABEL = "R"
RESP_REQ_GET_A = 'R.json'
W_LABEL = "W"
REQ_GET_E = 'W.json'
RESP_REQ_GET_E = REQ_GET_E
E_LABEL = "e"
B_LABEL = "W"

# OT 1 of n
REQ_GET_C = 'get_c'
C_LABEL = 'C'
RESP_REQ_GET_C = 'C.json'

def hashki(k, i):
    return hashlib.sha512(f'{k}{i}'.encode()).hexdigest()

assert len(hashki("x", 1)) <= K_SIZE, f'{len(hashki("x", 1))}, {K_SIZE}'

class Sender:
    class Sender1Of2:
        def __init__(self, m0 : str, m1 : str) -> None:
            self.m = [m0, m1]
            self.Q = mcl.G1().hashAndMapTo(f'{m0}{m1}'.encode())
            self.step = 0

        def get_A(self):
            assert self.step == 0
            self.step += 1
            self.a = Fr.rnd()
            self.A = self.Q * self.a
            return self.A, self.Q

        def get_encrypted(self, B):
            assert self.step == 1
            self.step += 1
            k0 = Fr.setHashOf(f'{B*self.a}'.encode())
            k1 = Fr.setHashOf(f'{(B - self.A)*self.a}'.encode())

            e0 = xor_strings(self.m[0], k0.getStr().decode())
            e1 = xor_strings(self.m[1], k1.getStr().decode())

            return [e0, e1]

        def sender_process_function(self,file_data : bytes, filename : str, message : str):
            logging.info(f'\n\nSender1Of2 sender_process_function({file_data=}, {filename=}, {message=})')
            if message == REQ_GET_A:
                #
                processed_file_path = f'{SERVER_PATH}/{RESP_REQ_GET_A}'
                A, Q = self.get_A()
                mcljson.write_list_json(processed_file_path, A_LABEL, [A, Q])
                return processed_file_path
            if filename == REQ_GET_E:
                # print(f'{file_data.decode()=}, {E_LABEL=}')
                B = mcljson.read_list_json(file_data.decode(), B_LABEL)
                e = self.get_encrypted(B)
                processed_file_path = f'{SERVER_PATH}/{RESP_REQ_GET_E}'
                mcljson.write_list_json(processed_file_path, E_LABEL, e)
                return processed_file_path
            raise Exception(f'\n unprocessed request sender_process_function({file_data=}, {filename=}, {message=})')


        def is_finished(self):
            return self.step == 2

    def __init__(self, m : list[str]) -> None:

        self.m = m
        self.n = len(m)
        self.ot_1of2_sender = None
        self.ot_1of2_to_run = 0
        self.l = math.ceil(math.log2(self.n))

        # gen pairs k
        def gen_k() -> str:
            random_text = secrets.token_urlsafe(K_SIZE)
            return random_text[:K_SIZE]
        self.k_pairs = []
        for i in range(self.l):
            k_0 = gen_k()
            k_1 = gen_k()
            self.k_pairs.append((k_0, k_1))

        self.ot_counter = 0

    def encrypt_j(self, j : int, message : str):
        """Return C_j

        Args:
            j (int): index
            message (str): message to ecnrypt
        """

        cj = message
        for i in range(self.l):
            ki = self.k_pairs[i][get_ith_bit(j, i)]
            fk = ''
            for i in range(K_NUM):
                fk += hashki(ki, i)
            cj = xor_strings(cj, fk)

        return cj

    def get_c(self):
        c = [self.encrypt_j(j, m) for j, m in enumerate(self.m)]
        return c

    def sender_process_function(self,file_data : bytes, filename : str, message : str):
        print(f'[SENDER] sender_process_function({file_data=}, {filename=}, {message=})')
        if self.ot_1of2_to_run > 0:
            if self.ot_1of2_sender is None:
                self.ot_1of2_sender = \
                     self.Sender1Of2(*self.k_pairs[self.ot_counter])
            ret = self.ot_1of2_sender.sender_process_function(file_data, filename, message)
            if self.ot_1of2_sender.is_finished():
                self.ot_1of2_to_run -= 1
                self.ot_counter += 1
                self.ot_1of2_sender = None
            return ret

        if message == REQ_GET_C:
            self.ot_1of2_to_run = len(self.k_pairs)
            self.ot_counter = 0
            C = self.get_c()
            processed_file_path = f'{SERVER_PATH}/{RESP_REQ_GET_C}'
            mcljson.write_list_json(processed_file_path, C_LABEL, C)
            assert processed_file_path is not None
            return processed_file_path
        raise Exception(f'\n[SENDER] unprocessed request sender_process_function({file_data=}, {filename=}, {message=})')







class Receiver:
    class Receiver1Of2:
        def __init__(self, c : int, server_url : str) -> None:
            self.c = c
            self.server_url = server_url

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

        def run_ot(self) -> str:
            # A = sender.get_A()
            response_json = \
                client.send_message_to_server(REQ_GET_A, self.server_url)
            print(f'{response_json=}')
            AQ = mcljson.read_list_json(response_json, A_LABEL)
            A = AQ[0]
            self.Q = AQ[1]

            B = self.get_B(A)
            processed_file_path = f'{CLIENT_PATH}/{REQ_GET_E}'
            mcljson.write_list_json(processed_file_path, B_LABEL, B)
            response_json = \
                client.send_file_to_server(processed_file_path, self.server_url)
            # e = read_list_json(response_json, "e")
            e = json.loads(response_json)[E_LABEL]
            return self.decrypt(e)


    def __init__(self, i : int, n, server_url : str) -> None:
        self.j = i
        self.server_url = server_url
        self.l = math.ceil(math.log2(n))

    def run_ot_1of2(self):
        self.k = []
        for i in range(self.l):
            bit = get_ith_bit(self.j, i)
            rec = self.Receiver1Of2(bit, self.server_url)
            ki = rec.run_ot()
            self.k.append(ki)

    def decrypt(self, cipher : str):
        plain = cipher
        for i in range(self.l):
            ki = self.k[i]
            fk = ''
            for i in range(K_NUM):
                fk += hashki(ki, i)
            plain = xor_strings(plain, fk)
        return remove_trailing_zeros(plain)

    def run_ot(self):
        response_json = client.send_message_to_server(REQ_GET_C, self.server_url)
        # print(f'{response_json=}')
        C = mcljson.read_list_json(response_json, C_LABEL)
        self.run_ot_1of2()
        print(self.k)
        return self.decrypt(C[self.j])



def parse_args_mode():
    if len(sys.argv) < 2:
        print('add argument both|server|client [url]')
        # exit(-1)
        return True, True, f'http://localhost:56000'
    mode : str = sys.argv[1]
    run_server : bool = mode == "server"
    run_client : bool = mode == "client"
    if mode == "both":
        run_server = True
        run_client = True
    PORT = 0

    if run_server:
        PORT = 56000
        server_url = f'http://localhost:{PORT}'
    else:
        if len(sys.argv) == 2:
            server_url = 'http://192.168.80.226:56000'
        else:
            server_url = sys.argv[2]
    return run_server, run_client, server_url



# run_server = False
# run_client_mode = True
# server_url = 'http://192.168.80.226:8000'
# time.sleep(10)
def main():
    # Configure logging for the client
    logging.basicConfig(level=logging.INFO, filename='client.log', filemode='a',
                        format='%(asctime)s - %(levelname)s - %(message)s')

    run_server_mode, run_client_mode,server_url = parse_args_mode()
    PORT = int(server_url.split(':')[-1])


    # comon params
    Q = G1().hashAndMapTo(b'test')
    N = 1000

    if run_server_mode:
        # global params
        m = [mcljson.mcl_to_str(Fr(i)) for i in range(N)]
        #  m = [f'message {i:_<100}' for i in range(N)]
        assert not any({len(mi) > M_SIZE for mi in m})
        l = math.ceil(math.log2(N))

        # set_xor_max_len(M_SIZE)
        print(f'{N=}')
        print(f'{l=}')
        print(f'{K_NUM=}')

        def sender_process_function(file_data : bytes, filename : str, message : str):
            return sender.sender_process_function(file_data, filename, message)

        def run_server():
            global sender
            sender = Sender(m)
            server.run_server(sender_process_function, port=PORT)


        server_thread = threading.Thread(target=run_server)
        server_thread.start()
        time.sleep(2)


    if run_client_mode:
        i = 100 % N
        for k in range(1):
            receiver = Receiver(i, N, server_url=server_url)
            mc = receiver.run_ot()
        # check for success
        print(f'received: {mc.encode()}')
        print(f'received: {mcljson.mcl_from_str(mc, Fr)}')

        # print(f'{m[i].encode()}; {mc.encode()};')
        # print(f'{m[i]=}; {mc=};')

        success = m[i] == mc
        if success:
            print('Success')
        else:
            print('Failed')

if __name__ == '__main__':
    main()


