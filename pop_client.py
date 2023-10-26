
from cProfile import label
from http import client
from tempfile import tempdir
import mcl

from functools import reduce

Z = 8

def get_fr(val : int):
    x = mcl.Fr()
    x.setInt(val)
    return x


def lagrange_interpolation(x, phi):
    def term(i):
        xi, yi = phi[i]
        numerator = [(x - phi[j][0]) for j in range(len(phi)) if j != i]
        denominator = [(xi - phi[j][0]) for j in range(len(phi)) if j != i]
        return yi * (reduce(lambda x,y : x *y, numerator) / reduce(lambda x,y : x *y, denominator))

    return reduce(lambda x,y : x+y, [term(i) for i in range(len(phi))])
    # interpolation = mcl.G1()
    # for point_1 in phi:
    #     x_i, y_i = point_1
    #     multi = mcl.Fr()
    #     multi.setInt(1)
    #     for point_2 in phi:
    #             x_j, y_j = point_2
    #             if x_i != x_j:
    #                 multi *= (x - x_j) / (x_i - x_j)
    #     multi = y_i * multi
    #     interpolation += multi
    # return interpolation


def eval_poly_horner(coefficients, x):
    result = get_fr(0)
    for coefficient in coefficients:
        result = result * x + coefficient
    return result


# def eval_poly(P, x) -> mcl.Fr:
#     y = mcl.Fr()
#     y.setInt(0)
#     for i, a in enumerate(P):
#         y += horner_exponential(x, i) * a
#     # print(y)
#     return y

def fr_to_str(fr : mcl.Fr):
    return fr.serialize().hex()

def fr_from_str(fr_str : str):
    fr = mcl.Fr()
    fr.deserialize(bytes.fromhex(fr_str))
    return fr


class Client:
    def __init__(self, file_name) -> None:
        self.file_name = file_name
        self.sk = mcl.Fr.rnd()
        self.LF = None


    def POLY(self, IDf, length):
        A = [
            mcl.Fr.setHashOf(f'{self.sk}{IDf}{i}'.encode())
            for i in range(length)]
        return A

    def save_to_file(self, path):
        print(self.sk)
        json_dict = {
            "sk" : fr_to_str(self.sk),
            "poly" : [fr_to_str(a) for a in self.LF],
            "file" : self.file_name
        }
        # print(json.dumps(json_dict, indent=2))

        with open(path, 'w') as fd:
            fd.write(json.dumps(json_dict,indent=2))
            # json.dump(fd, json_dict)

    def load_from_file(self, path):
        with open(path, 'r') as fd:
            file = fd.read()
            json_dict = json.loads(file)
            # print(json_dict)
            self.sk = fr_from_str(json_dict["sk"])
            self.LF = [
                fr_from_str(a) for a in json_dict["poly"]
            ]
            self.file_name = json_dict["file"]

    def get_file_tokens(self):
        # print(self.LF)
        CHUNK_SIZE = 1
        M = []
        with open(self.file_name, 'rb') as fd:
            while True:
                data = fd.read(CHUNK_SIZE)
                if data == b'':
                    break
                mi = get_fr(int.from_bytes(data, byteorder='little'))
                M.append(mi)
                # print(f'{data=} {mi=}')

        self.LF = self.POLY(self.file_name, len(M) + 1)
        # print(f'{len(self.LF)=}')
        # print(self.LF)
        Tf = [
            (mi, eval_poly_horner(self.LF, mi))
            for mi in M
        ]
        print('client:')
        print(f'{Tf=}')
        print(f'{len(Tf)=}')

        return Tf


    def gen_challenge(self):
        r = mcl.Fr.rnd()
        x = mcl.Fr.rnd()
        # r = get_fr(12345)
        # r = self.sk
        # x = get_fr(123456)

        Q = mcl.G1().hashAndMapTo(b'genQ')
        Qr = Q*r
        Kf = Qr * eval_poly_horner(self.LF, x)
        # H = (Qr, x, Qr*eval_poly_horner(self.LF, get_fr(0)))
        H = (Qr, x, Qr*self.LF[-1])

        self.Kf = Kf

        return  H

    def check_challenge(self, Pf):
        print(f'{self.Kf=}')
        print(f'{Pf=}')

        return self.Kf == Pf






import json
def read_proof_from_json(path : str):
    with open(path, 'r') as fd:
        json = json.load(fd)

        return mcl.G1(json['proof'])

# def write_proof_to_json(path : str, pf : mcl.G1):
#     with open(path, 'r') as fd:
#         json_dict = {
#             "proof" : pf.getStr()
#         }
#         json.dump(fd, json_dict)

import sys


if len(sys.argv) == 1 :
    file_name = "test_file.txt"
else:
    file_name = sys.argv[1]

print(file_name)

client = Client(file_name)
# cloud = Cloud()
tokens = client.get_file_tokens()
# cloud.upload(tokens)

# send to json
client.save_to_file("client.json")
client.load_from_file("client.json")

H = client.gen_challenge()


# read Pf

# Pf = read_proof_from_json("response.json")

# print(f'{Q=}\n{H=}')
# print(client.Kf)
# Pf = cloud.verify(H)
# print(Pf)



# print(client.check_challenge(Pf))