import random
import mcl
import time

# mcl.mcl_init(mcl.CurveType.MCL_BLS12_381)

def hash_challenge(file, challenge):
    with open(file, 'br') as fd:
        f_string = fd.read()
        hash_challenge = f'{f_string}{challenge}'
        return mcl.Fr.setHashOf(hash_challenge.encode())

# client
class Client:
    def __init__(self, c_len, file) -> None:
        self.c_len = c_len
        self.C = [
            mcl.Fr().setByCSPRNG() for _ in range(c_len)
        ]
        self.H = [
            hash_challenge(file, c) for c in self.C
        ]

    def get_challenge(self):
        idx = random.randint(0, self.c_len)
        return self.C[idx], self.H[idx]

    def check_challenge(self, c, h_cloud):
        idx = self.C.index(c)
        h = self.H[idx]
        return h == h_cloud

class Cloud:
    def __init__(self, file) -> None:
        self.file = file

    def check(self, challenge):
        return hash_challenge(file, challenge)

file = 'README.md'
c_len = 11

client = Client(c_len, file)
cloud = Cloud(file)

c, h = client.get_challenge()
h_c = cloud.check(c)

success = client.check_challenge(c, h_c)

print(f'success {success}')
