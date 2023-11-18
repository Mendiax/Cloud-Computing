import secrets
from mcl import *

import math
import time
import threading

import logging
import sys
import hashlib
import json


import server
import client
import mcljson
import utilities

import ot_1of2_server



CLIENT_PATH = 'client'
SERVER_PATH = 'server'



# OT 1 of n
OT_1OfN_REQ_GET_C = 'get_c'
OT_1OfN_C_LABEL = 'C'
OT_1OfN_Q_LABEL = 'Q'
OT_1OfN_M_SIZE_LABEL = 'M_SIZE'


def hashki(k, i):
    return hashlib.sha512(f'{k}{i}'.encode()).hexdigest()


class Sender1OfN:
    def __init__(self, m : list[str], limit=100) -> None:
        self.m = m
        self.n = len(m)
        self.ot_1of2_sender = None
        self.ot_1of2_to_run = 0
        self.l = math.ceil(math.log2(self.n))
        self.Q = G1().hashAndMapTo(b'test')

        self.no_runs = 0
        self.limit = limit

        self.M_SIZE = len(max(m, key=len)) # bytes
        self.K_SIZE = len(hashki("x", 1))
        self.K_NUM = math.ceil((self.M_SIZE) / self.K_SIZE)
        utilities.set_xor_max_len(self.K_NUM * self.K_SIZE)

        print('Params:')
        print(f'{self.M_SIZE=}')
        print(f'{self.K_SIZE=}')
        print(f'{self.K_NUM=}')
        print(f'{self.n=}')
        print(f'{self.l=}')


    @staticmethod
    def get_addr():
        return '1ofN'

    def encrypt_j(self, j : int, message : str):
        cj = message
        for i in range(self.l):
            ki = self.k_pairs[i][utilities.get_ith_bit(j, i)]
            fk = ''
            for i in range(self.K_NUM):
                fk += hashki(ki, i)
            cj = utilities.xor_strings(cj, fk)

        return cj

    def get_c(self):
        c = [self.encrypt_j(j, m) for j, m in enumerate(self.m)]
        return c

    def sender_process_function(self, addr, message, payload):
        if addr == ot_1of2_server.Sender1Of2.get_addr():
            if self.ot_1of2_sender is None:
                self.ot_1of2_sender = \
                     ot_1of2_server.Sender1Of2(self.Q, *self.k_pairs[self.ot_counter])
            ret = self.ot_1of2_sender.sender_process_function(addr, message, payload)
            if self.ot_1of2_sender.is_finished():
                self.ot_counter += 1
                self.ot_1of2_sender = None
            return ret

        if addr != self.get_addr():
            raise Exception(f'Address {addr} not handled')
        print(f'Sender1OfN sender_process_function({message=}, {payload=})')

        if message == OT_1OfN_REQ_GET_C:
            assert self.no_runs < self.limit
            self.no_runs += 1

            # gen pairs k
            def gen_k() -> str:
                random_text = secrets.token_urlsafe(self.K_SIZE)
                return random_text[:self.K_SIZE]
            self.k_pairs = []
            for _ in range(self.l):
                k_0 = gen_k()
                k_1 = gen_k()
                self.k_pairs.append((k_0, k_1))

            self.ot_counter = 0
            C = self.get_c()
            return mcljson.dict_to_json({OT_1OfN_C_LABEL: C, OT_1OfN_Q_LABEL: self.Q, OT_1OfN_M_SIZE_LABEL: self.M_SIZE})
        raise Exception(
            f'\n[SENDER] unprocessed request sender_process_function({message=}, {payload=})')







class Receiver1OfN:
    def __init__(self, i : int, server_url : str) -> None:
        self.j = i
        self.server_url = server_url


    def run_ot_1of2(self):
        self.k = []
        for i in range(self.l):
            bit = utilities.get_ith_bit(self.j, i)
            rec = ot_1of2_server.Receiver1Of2(self.Q, bit, self.server_url)
            ki = rec.run_ot()
            self.k.append(ki)

    def decrypt(self, cipher : str):
        plain = cipher
        for i in range(self.l):
            ki = self.k[i]
            fk = ''
            for i in range(self.K_NUM):
                fk += hashki(ki, i)
            plain = utilities.xor_strings(plain, fk)
        return utilities.remove_trailing_zeros(plain)

    def run_ot(self):
        response_json = client.send_message_to_server(self.server_url, Sender1OfN.get_addr(), OT_1OfN_REQ_GET_C)
        # print(f'{response_json=}')
        CQ_json = mcljson.json_to_dict(response_json)

        # update m length parameter
        M_SIZE = int(CQ_json[OT_1OfN_M_SIZE_LABEL])
        K_SIZE = len(hashki("x", 1))
        self.K_NUM = math.ceil((M_SIZE) / K_SIZE)
        # utilities.set_xor_max_len(M_SIZE)
        utilities.set_xor_max_len(self.K_NUM * K_SIZE)

        C = CQ_json[OT_1OfN_C_LABEL]
        self.l = math.ceil(math.log2(len(C)))


        self.Q = mcljson.mcl_from_str(CQ_json[OT_1OfN_Q_LABEL], G1)
        self.run_ot_1of2()
        # print(self.k)
        return self.decrypt(C[self.j])



def main():
    # Configure logging for the client
    logging.basicConfig(level=logging.INFO, filename='client.log', filemode='a',
                        format='%(asctime)s - %(levelname)s - %(message)s')

    run_server_mode, run_client_mode,server_url = utilities.parse_args_mode()
    PORT = int(server_url.split(':')[-1])

    if run_server_mode:
        N = 1000
        # global params
        m = [mcljson.mcl_to_str(Fr(i)) for i in range(N)]
        #  m = [f'message {i:_<100}' for i in range(N)]
        # l = math.ceil(math.log2(N))
        # # set_xor_max_len(M_SIZE)


        def sender_process_function(addr, message, payload):
            return sender.sender_process_function(addr, message, payload)
        def run_server():
            global sender
            sender = Sender1OfN(m)
            server.run_server(sender_process_function, port=PORT)
        server_thread = threading.Thread(target=run_server)
        server_thread.start()
        time.sleep(3)


    if run_client_mode:
        i = 100
        for k in range(1):
            receiver = Receiver1OfN(i, server_url)
            mc = receiver.run_ot()
        # check for success
        print(f'received: {mc}')
        print(f'received: {mcljson.mcl_from_str(mc, Fr)}')

        if run_server_mode:
            success = m[i] == mc
            if success:
                print('Success')
            else:
                print('Failed')

if __name__ == '__main__':
    main()


