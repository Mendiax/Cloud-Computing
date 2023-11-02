from mcl import *

from utilities import *



class Sender:
    def __init__(self, Q : G1, m0 : str, m1 : str) -> None:
        self.m = [m0, m1]
        self.Q = Q

    def get_A(self):
        self.a = Fr.rnd()
        self.A = self.Q * self.a
        return self.A

    def get_encrypted(self, B):
        k0 = Fr.setHashOf(f'{B*self.a}'.encode())
        k1 = Fr.setHashOf(f'{(B - self.A)*self.a}'.encode())

        e0 = xor_strings(self.m[0], k0.getStr().decode())
        e1 = xor_strings(self.m[1], k1.getStr().decode())

        return [e0, e1]




class Receiver:
    def __init__(self, Q : G1, c : int) -> None:
        self.c = c
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

        m = xor_strings(self.kr.getStr().decode(), ec)
        return remove_trailing_zeros(m)


Q = G1().hashAndMapTo(b'test')

m = ["message 1", "message 2"]
c = 0
sender = Sender(Q, *m)
receiver = Receiver(Q, c)

A = sender.get_A()
B = receiver.get_B(A)
e = sender.get_encrypted(B)
mc = receiver.decrypt(e)

assert m[c] == mc, f'{m[c].encode()}; {mc.encode()};'
print(f'{m[c]=}; {mc=};')




