
from cProfile import label
from http import client
from tempfile import tempdir
import mcl
import json
import mcljson
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


def eval_poly_horner(coefficients, x):
    result = get_fr(0)
    for coefficient in coefficients:
        result = result * x + coefficient
    return result






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
        # json_dict = {
        #     "sk" : fr_to_str(self.sk),
        #     "poly" : [fr_to_str(a) for a in self.LF],
        #     "file" : self.file_name
        # }
        json_dict = {
            "sk" : self.sk,
            "poly" : [a for a in self.LF],
            "file" : self.file_name
        }
        # print(json.dumps(json_dict, indent=2))
        mcljson.write_json_mcl(path, json_dict)

        # with open(path, 'w') as fd:
        #     fd.write(json.dumps(json_dict,indent=2, cls=mcljson.mclEncoder))
        #     # json.dump(fd, json_dict)

    def load_from_file(self, path):
        # json_dict = mcljson.read_json_mcl(path)
        # self.sk = json_dict["sk"]
        # self.LF = json_dict["poly"]
        # self.file_name = json_dict["file"]
        with open(path, 'r') as fd:
            file = fd.read()
            json_dict = json.loads(file, cls=mcljson.mclDecoder)
            print(json_dict)
            # self.sk = fr_from_str(json_dict["sk"])
            # self.LF = [
            #     fr_from_str(a) for a in json_dict["poly"]
            # ]
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