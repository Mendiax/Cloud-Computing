
from http import client
import mcl
import mcljson

from typing import List, Tuple, Any, Union

from functools import reduce


def get_fr(val : int):
    x = mcl.Fr()
    # print(f'{val=}')
    x.setInt(val)
    return x


def lagrange_interpolation(x, phi):
    def term(i):
        xi, yi = phi[i]
        numerator = [(x - phi[j][0]) for j in range(len(phi)) if j != i]
        denominator = [(xi - phi[j][0]) for j in range(len(phi)) if j != i]
        return yi * (reduce(lambda x,y : x *y, numerator) / reduce(lambda x,y : x *y, denominator))

    return reduce(lambda x,y : x+y, [term(i) for i in range(len(phi))])


def eval_poly_horner(coefficients, x):
    result = get_fr(0)
    for coefficient in coefficients:
        result = result * x + coefficient
    return result


BITS_PER_IDX = 4
BYTES_PER_IDX = 4


def convert_bytes_to_int(bytes, chunk_id):
    return int.from_bytes(bytes, byteorder='little') + chunk_id

def convert_bytes_to_fr(bytes, chunk_id):
    # assert chunk_id < 2**BITS_PER_IDX
    mi = mcl.Fr()
    # mi.setStr(bytes)
    mi = get_fr(convert_bytes_to_int(bytes, chunk_id))
    # mi.setStr(str(convert_bytes_to_int(bytes, chunk_id)))

    return mi

# def convert_bytes_to_fr(chunk : bytes, chunk_id : int):
#     assert chunk_id < 2**(BYTES_PER_IDX * 8)
#     mi = mcl.Fr()
#     # chunk_idx = chunk_id.to_bytes(BYTES_PER_IDX, byteorder='big')
#     # chunk_idx = f'{hex(chunk_id)[2:].upper():0>8}'.encode(encoding='ascii')
#     chunk_idx = hex(chunk_id)[2:].upper()
#     chunk_idx = f"{'0' * (BYTES_PER_IDX - len(chunk_idx))}" + chunk_idx
#     print(chunk_idx)
#     chunk_idx = chunk_idx.encode(encoding='latin-1')

#     # print(f'{chunk_id=}')
#     print(chunk)
#     # print(chunk_idx)
#     print(chunk + chunk_idx)
#     # print(type(chunk))
#     # print(type(chunk_idx))
#     mi.setStr(chunk + chunk_idx)
#     print(mi)

#     return mi

def convert_fr_to_bytes(fr : mcl.Fr):
    print(fr)
    fr_str = fr.getStr()[:-BYTES_PER_IDX]
    print(fr_str)
    return fr_str


class Client:
    def __init__(self, file_name) -> None:
        self.file_name = file_name
        self.sk = mcl.Fr.rnd()



    def POLY(self, IDf, length):
        A = [
            mcl.Fr.setHashOf(f'{self.sk}{IDf}{i}'.encode())
            for i in range(length + 1)]
        return A


    def get_file_tokens(self):
        # print(self.LF)
        CHUNK_SIZE = 4
        M = []
        chunk_id = 1
        with open(self.file_name, 'rb') as fd:
            while True:
                data = fd.read(CHUNK_SIZE)
                if data == b'':
                    break
                # print(f'{data=}')
                # assert chunk_id < 2**16
                # mi = get_fr(int.from_bytes(data, byteorder='little') << 16 + chunk_id)
                M.append(data)

                # chunk_fr = convert_bytes_to_fr(data, chunk_id)
                # d2 = data
                # d1 = convert_fr_to_bytes(chunk_fr)
                # assert d1 == d2, f'{d1}, {d2}, {chunk_fr}'
                # chunk_id += 1
                # print(f'{data=} {mi=}')

        self.LF = self.POLY(self.file_name, len(M))
        # print(f'{len(self.LF)=}')
        # print(self.LF)
        Tf = [
            (mi, eval_poly_horner(self.LF, convert_bytes_to_fr(mi, i)))
            for i, mi in enumerate(M)
        ]
        # print('client:')
        # print(f'{Tf=}')
        # print(f'{len(Tf)=}')

        return Tf


    def gen_challenge(self):
        r = mcl.Fr.rnd()
        x = mcl.Fr.rnd()
        # r = get_fr(456)
        # x = get_fr(789)

        Q = mcl.G1().hashAndMapTo(b'test')
        Qr = Q*r
        Kf = Qr * eval_poly_horner(self.LF, x)
        print(Q)
        H = (Qr, x, Qr*eval_poly_horner(self.LF, get_fr(0)))
        # H = (Qr, x, Qr*self.LF[-1])

        self.Kf = Kf
        print(f'{self.Kf=}')

        return  H

    def check_challenge(self, Pf):
        print(f'{self.Kf=}')
        print(f'{Pf=}')

        return self.Kf == Pf



class Cloud:
    def __init__(self) -> None:
        pass

    def upload(self, Tf):
        self.Tf = Tf

    def verify(self, H):
        Qr, x, Qrl = H
        psi = [(get_fr(0), Qrl)]
        for i, (mi,ti) in  enumerate(self.Tf):
            # data_val = int.from_bytes(mi, byteorder='little')
            m = convert_bytes_to_fr(mi, i)
            psi.append((m, Qr * ti))

        return lagrange_interpolation( x, psi)

    def get_file(self, path_to_save : str):
        with open(path_to_save, 'bw') as fd:
            for mi, ti in self.Tf:
                fd.write(mi)

    @staticmethod
    def deserialize_tagged_file(json_data: List[List[Union[str, bytes]]]) -> List[Tuple[bytes, mcl.Fr]]:
        deserialized_data = []
        for item in json_data:
            if len(item) == 2:
                raw_data = bytes(item[0], 'latin-1')
                fr_value_ = mcl.Fr()
                fr_value_.setStr(bytes(item[1], 'latin-1'))
                deserialized_data.append((raw_data, fr_value_))
        return deserialized_data

    @staticmethod
    def deserialize_challenge(json_data: List[str]) -> Tuple[mcl.G1, mcl.Fr, mcl.G1]:
        g_value__ = mcl.G1()
        x_value_ = mcl.Fr()
        g_coefficient__ =mcl. G1()

        if len(json_data) == 3:
            g_value__.setStr(bytes(json_data[0], 'latin-1'))
            x_value_.setStr(bytes(json_data[1], 'latin-1'))
            g_coefficient__.setStr(bytes(json_data[2], 'latin-1'))
        return g_value__, x_value_, g_coefficient__



import sys

print(sys.argv)
if len(sys.argv) == 2 :
    file_name = "./data/test_file.txt"
else:
    file_name = sys.argv[2]

print(file_name)
run_client = (sys.argv[1] == "client")
run_cloud = (sys.argv[1] == "cloud")

# folder = '/home/bartek/cdrive/Users/Ja/Downloads/'
# folder = '/home/bartek/cdrive/Users/Ja/Downloads/witek/'
folder = './data/'

if sys.argv[1] == "both":
    run_client = True
    run_cloud = True

if run_client:
    client = Client(file_name)
if run_cloud:
    cloud = Cloud()

# import os
# import glob

# files = glob.glob('./data/*')
# for f in files:
#     os.remove(f)



if run_client:
    input("start")
    # client
    tokens = client.get_file_tokens()
    # tokens.pop()
    print(f'{len(tokens)=}')
    tagged_file = folder + 'tagged_file.json'
    mcljson.save_to_json(tagged_file, tokens)
    print(f"written tagged file {tagged_file}")


if run_cloud:
    input("read tagged ")
    # cloud
    loaded_data = mcljson.load_from_json(folder + 'tagged_file.json')
    # print(tokens)
    cloud.upload(cloud.deserialize_tagged_file(loaded_data))



if run_client:
    #  client
    H = client.gen_challenge()
    # print(client.Kf)
    challenge_file = folder + 'challenge.json'
    mcljson.save_to_json(challenge_file, H)
    print(f'written challenge {challenge_file}')

if run_cloud:
    input("read challenge")
    # cloud
    loaded_challenge = mcljson.load_from_json(folder + 'challenge.json')
    cloud_challenge = cloud.deserialize_challenge(loaded_challenge)
    Pf = cloud.verify(cloud_challenge)
    print(Pf)
    mcljson.save_to_json(folder + 'proof_file.json', Pf)



if run_client:
    input("proof")
    loaded_proof_file__ = mcljson.load_from_json(folder + 'proof_file.json')
    if isinstance(loaded_proof_file__, str):
        proof_file__ = mcl.G1()
        proof_file__.setStr(bytes(loaded_proof_file__, 'latin-1'))
        if client.check_challenge(proof_file__):
            print("Proof verified!")
        else:
            print("Proof failed!")
# print(f'{client.check_challenge(Pf)=}')


# # client
# file_output = 'output.txt'
# cloud.get_file(file_output)
# import filecmp
# identical = filecmp.cmp(file_name, file_output)
# print(f'{identical=}')
# assert(identical)