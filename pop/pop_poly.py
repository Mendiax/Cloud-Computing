
from cProfile import label
from http import client
from tempfile import tempdir
import mcl

from functools import reduce


def get_fr(val : int):
    x = mcl.Fr()
    # print(f'{val=}')
    x.setInt(val)
    return x

# def exponential(x, y):
#     if x.isZero():
#         return get_fr(0)
#     if y == 0:
#         return get_fr(1)
#     r = mcl.Fr()
#     r.setInt(1)
#     # print(y)
#     for i in range(y):
#         r = r * x
#     return r

# def horner_exponential(x, n):
#     result = get_fr(1)
#     one = get_fr(1)
#     for i in range(n, 0, -1):
#         i_fr = get_fr(i)
#         result = one + ((x / i_fr) * result)
#     return result


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


BITS_PER_IDX = 4
BYTES_PER_IDX = 4


def convert_bytes_to_int(bytes, chunk_id):
    return int.from_bytes(bytes, byteorder='little') + chunk_id

def convert_bytes_to_fr(bytes, chunk_id):
    assert chunk_id < 2**BITS_PER_IDX
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
                print(f'{data=}')
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




import sys


if len(sys.argv) == 1 :
    file_name = "test_file.txt"
else:
    file_name = sys.argv[1]

print(file_name)

client = Client(file_name)
cloud = Cloud()
tokens = client.get_file_tokens()
# tokens.pop()
print(f'{len(tokens)=}')
# print(tokens)
cloud.upload(tokens)

H = client.gen_challenge()

# print(f'{Q=}\n{H=}')
# print(client.Kf)
Pf = cloud.verify(H)
# print(Pf)



print(f'{client.check_challenge(Pf)=}')

file_output = 'output.txt'
cloud.get_file(file_output)

import filecmp
identical = filecmp.cmp(file_name, file_output)
print(f'{identical=}')
assert(identical)