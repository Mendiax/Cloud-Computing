
from cProfile import label
from http import client
from tempfile import tempdir
import mcl

from functools import reduce

Z = 10

def get_fr(val : int):
    x = mcl.Fr()
    x.setInt(val)
    return x

def exponential(x, y):
    if x.isZero():
        return get_fr(0)
    if y == 0:
        return get_fr(1)
    r = mcl.Fr()
    r.setInt(1)
    # print(y)
    for i in range(y):
        r = r * x
    return r


def lagrange_interpolation(Q, x, phi):
    def term(i):
        xi, yi = phi[i]
        numerator = [(x - phi[j][0]) for j in range(len(phi)) if j != i]
        denominator = [(xi - phi[j][0]) for j in range(len(phi)) if j != i]
        return yi * (reduce(lambda x,y : x *y, numerator) / reduce(lambda x,y : x *y, denominator))

    return reduce(lambda x,y : x+y, [term(i) for i in range(len(phi))])




def eval_poly(P, x) -> mcl.Fr:
    y = mcl.Fr()
    y.setInt(0)
    for i, a in enumerate(P):
        y += a*exponential(x, i)
    # print(y)
    return y


class Client:
    def __init__(self, file_name) -> None:
        self.file_name = file_name
        self.sk = mcl.Fr.rnd()

    def POLY(self, IDf):
        A = [
            mcl.Fr.setHashOf(f'{self.sk}{IDf}{i}'.encode())
            for i in range(Z)]
        return A



    def get_file_tokens(self):
        self.LF = self.POLY(self.file_name)
        # print(self.LF)
        CHUNK_SIZE = 8
        Tf = []
        with open(self.file_name, 'rb') as fd:
            while True:
                data = fd.read(CHUNK_SIZE)
                if data == b'':
                    break
                mi = get_fr(int.from_bytes(data, byteorder='little'))
                Tf.append((mi, eval_poly(self.LF, mi)))

        return Tf

    def gen_challenge(self):
        r = mcl.Fr.rnd()
        x = mcl.Fr.rnd()
        Q = mcl.G1().hashAndMapTo(b'123')
        Kf = Q * (r * eval_poly(self.LF, x))
        H = (Q*r, x, Q*(r*self.LF[0]))

        self.Kf = Kf

        return Q, H

    def check_challenge(self, Pf):
        return self.Kf == Pf




class Cloud:

    def __init__(self) -> None:
        pass

    def upload(self, Tf):
        self.Tf = Tf

    def verify(self, Q : mcl.G1, H):
        Qr, x, Qrl = H
        psi = [(get_fr(0), Qrl)]
        for mi,ti in  self.Tf:
            # data_val = int.from_bytes(mi, byteorder='little')
            psi.append((mi, Qr * ti))

        return lagrange_interpolation(Q, x, psi)





file_name = "test_file.txt"

client = Client(file_name)
cloud = Cloud()

cloud.upload(client.get_file_tokens())

Q, H = client.gen_challenge()
# print(f'{Q=}\n{H=}')
# print(client.Kf)
Pf = cloud.verify(Q,H)
# print(Pf)



print(client.check_challenge(Pf))