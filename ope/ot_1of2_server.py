from mcl import *

import time
import threading
import logging
import sys


import utilities
import server
import client
import mcljson

OT_1Of2_REQ_GET_A = 'req_a'
OT_1Of2_REQ_GET_E = 'req_e'
OT_1Of2_E_LABEL = 'e'


CLIENT_PATH = 'client'
SERVER_PATH = 'server'


# Configure logging for the client
logging.basicConfig(level=logging.INFO, filename='client.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')


class Sender1Of2:
    def __init__(self, Q : G1, m0 : str, m1 : str, limit=1) -> None:
        self.m = [m0, m1]
        self.Q = Q
        self.step = 0

        self.no_runs = 0
        self.limit = limit

    @staticmethod
    def get_addr():
        return '1of2'

    def get_A(self):
        self.step = 1
        self.a = Fr.rnd()
        self.A = self.Q * self.a
        return self.A

    def get_encrypted(self, B):
        assert self.step == 1, 'wrong step'
        self.step += 1
        k0 = Fr.setHashOf(f'{B*self.a}'.encode())
        k1 = Fr.setHashOf(f'{(B - self.A)*self.a}'.encode())

        e0 = utilities.xor_strings(self.m[0], k0.getStr().decode())
        e1 = utilities.xor_strings(self.m[1], k1.getStr().decode())

        return [e0, e1]

    def sender_process_function(self, addr, message, payload):
        if addr != self.get_addr():
            raise Exception(f'Address {addr} not handled')
        print(f'Sender1Of2 sender_process_function({message=}, {payload=})')
        if message == OT_1Of2_REQ_GET_A:
            assert self.no_runs < self.limit
            self.no_runs += 1
            A = self.get_A()
            return mcljson.mcl_to_str(A)
        if message == OT_1Of2_REQ_GET_E:
            # print(f'{file_data.decode()=}, {E_LABEL=}')
            B = mcljson.mcl_from_str(payload, G1)
            e = self.get_encrypted(B)
            return mcljson.dict_to_json({OT_1Of2_E_LABEL : e})
        raise Exception(f'\n unprocessed request sender_process_function({message=}, {payload=})')


    def is_finished(self):
        return self.step == 2



class Receiver1Of2:
    def __init__(self, Q : G1, c : int, server_url : str) -> None:
        self.c = c
        self.server_url = server_url
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

        m = utilities.xor_strings(self.kr.getStr().decode(), ec)
        return utilities.remove_trailing_zeros(m)

    def run_ot(self) -> str:
        # A = sender.get_A()
        response_json = \
            client.send_message_to_server(
                self.server_url, Sender1Of2.get_addr(), OT_1Of2_REQ_GET_A)
        print(f'{response_json=}')
        A = mcljson.mcl_from_str(response_json, G1)

        B = self.get_B(A)
        response_json = \
            client.send_message_to_server(
                self.server_url, Sender1Of2.get_addr(), OT_1Of2_REQ_GET_E, mcljson.mcl_to_str(B))
        e = mcljson.json_to_dict(response_json)[OT_1Of2_E_LABEL]
        return self.decrypt(e)



def main():
    run_server, run_client, server_url = utilities.parse_args_mode() # type: ignore
    PORT = int(server_url.split(':')[-1])


    Q = G1().hashAndMapTo(b'test')
    m = [f"message {i}" for i in range(2)]



    if run_server:
        def sender_process_function(addr, message, payload):
            return sender.sender_process_function(addr, message, payload)
        def run_server():
            global sender
            sender = Sender1Of2(Q, *m)
            server.run_server(sender_process_function, port=PORT)
        server_thread = threading.Thread(target=run_server)
        server_thread.start()
        time.sleep(3)


    if run_client:
        i = 0
        receiver = Receiver1Of2(Q, i, server_url)
        mc = receiver.run_ot()

        print(f'received: {mc}')


if __name__ == '__main__':
    main()
