from mcl import *

import math
import time
import threading

import random

import logging
import json
from functools import reduce


import server
import client
import mcljson
import utilities

import ot_1ofn_fast_server
import ot_1of2_server

OPE_SEND_XY = "send_xy"
OPE_XY_LABEL = "xy"


DEG_POLY = 10

# sec params
SEC_PARAM_M = 5
SEC_PARAM_K = 5

SEC_PARAM_N = SEC_PARAM_K * DEG_POLY + 1
SEC_PARAM_NM = SEC_PARAM_N * SEC_PARAM_M


class Poly:
    def __init__(self, deg: int, seed="123") -> None:
        self.coefficients = [
            Fr.setHashOf(f'{seed}{i}'.encode())
            for i in range(deg + 1)
        ]

    def deg(self):
        return len(self.coefficients) - 1

    def set_0(self, val : Fr):
        self.coefficients[-1] = val

    def eval_poly_horner(self, x):
        result = Fr(0)
        for coefficient in self.coefficients:
            result = result * x + coefficient
        return result

    @staticmethod
    def lagrange_interpolation(x, phi):
        def term(i):
            xi, yi = phi[i]
            numerator = [(x - phi[j][0]) for j in range(len(phi)) if j != i]
            denominator = [(xi - phi[j][0]) for j in range(len(phi)) if j != i]
            return yi * (reduce(lambda x, y: x * y, numerator) / reduce(lambda x, y: x * y, denominator))

        return reduce(lambda x, y: x+y, [term(i) for i in range(len(phi))])


class Cloud:
    def __init__(self, poly) -> None:
        self.run_1ofn = 0
        self.poly = poly

        self.k = SEC_PARAM_K
        self.d = poly.deg() * self.k

    @staticmethod
    def get_addr():
        return 'ope'

    def setup(self):
        self.poly_x = Poly(self.d, seed='asd')
        self.poly_x.set_0(Fr(0))

    def calc_q(self,x,y):
        return self.poly_x.eval_poly_horner(x) + self.poly.eval_poly_horner(y)

    def sender_process_function(self, addr, message, payload):
        print(f'{self.run_1ofn=}')
        if addr == ot_1ofn_fast_server.Sender1OfN.get_addr() or\
            addr == ot_1of2_server.Sender1Of2.get_addr():
            return self.sender_1ofn.sender_process_function(addr, message, payload)

        if addr != self.get_addr():
            raise Exception(f'Address {addr} not handled')
        print(f'[CLOUD] sender_process_function({message=}, {payload=})')
        if message == OPE_SEND_XY:
            self.setup()
            # print(f'{file_data.decode()=}, {E_LABEL=}')
            XY = json.loads(payload)[OPE_XY_LABEL]
            R = []
            for x_str,y_str in XY:
                x = mcljson.mcl_from_str(x_str, Fr)
                y = mcljson.mcl_from_str(y_str, Fr)
                q_xy = mcljson.mcl_to_str(self.calc_q(x,y))
                print(q_xy)
                R.append(q_xy)

            self.run_1ofn = SEC_PARAM_N
            print(R)
            self.sender_1ofn = ot_1ofn_fast_server.Sender1OfN(R, limit=SEC_PARAM_N)
            return ""
        raise Exception(f'\n[CLOUD] unprocessed request sender_process_function({message=}, {payload=})')




class User:
    def __init__(self, alpha, server_url) -> None:
        self.server_url = server_url
        self.alpha = alpha
        self.T = []

    def gen_xy(self, alpha):
        X = [
            Fr.setHashOf(str(random.random()).encode())
            for _ in range(SEC_PARAM_NM)
        ]
        self.S = Poly(SEC_PARAM_K)
        self.S.set_0(alpha)
        self.T = [
            i for i in range(SEC_PARAM_NM)
        ]
        while len(self.T) > SEC_PARAM_N:
            remove_index = random.randint(0, len(self.T) - 1)
            self.T.pop(remove_index)
        tags = [
            (x, self.S.eval_poly_horner(x)) if i in self.T else
            (x, Fr.setHashOf(str(random.random()).encode()))
            for i, x in enumerate(X)
        ]

        return tags

    def run_ope(self):
        xy = self.gen_xy(self.alpha)
        payload = mcljson.dict_to_json({OPE_XY_LABEL : xy})
        client.send_message_to_server(self.server_url, Cloud.get_addr(), OPE_SEND_XY, payload)
        print('Client runs n of N')
        R_str = [
                ot_1ofn_fast_server.Receiver1OfN(i, self.server_url).run_ot()
            for i in self.T
        ]
        X = [
            t[0] for i, t in enumerate(xy) if i in self.T
        ]
        R = [
            mcljson.mcl_from_str(r_str, Fr) for r_str in R_str
        ]
        # print(R)
        XR = [_ for _ in zip(X,R)]
        print(len(XR))

        return Poly.lagrange_interpolation(Fr(0), XR)


def main():
    # Configure logging for the client
    logging.basicConfig(level=logging.INFO, filename='client.log', filemode='a',
                        format='%(asctime)s - %(levelname)s - %(message)s')

    run_server_mode, run_client_mode, server_url = utilities.parse_args_mode()
    PORT = int(server_url.split(':')[-1])

    poly = Poly(DEG_POLY)

    # comon params
    # N = 1000

    if run_server_mode:
        def sender_process_function(addr, message, payload):
            return sender.sender_process_function(addr, message, payload)

        def run_server():
            global sender
            sender = Cloud(poly)
            server.run_server(sender_process_function, port=PORT)

        server_thread = threading.Thread(target=run_server)
        server_thread.start()
        time.sleep(2)

    if run_client_mode:
        alpha = Fr(3)
        receiver = User(alpha, server_url=server_url)
        result = receiver.run_ope()
        print('Done:')
        print(result)
        print(poly.eval_poly_horner(alpha))
        print('\n')


if __name__ == '__main__':
    main()
