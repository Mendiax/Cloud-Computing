from mcl import *

from utilities import *



class Sender:
    def __init__(self, Q : G1, m : list[str]) -> None:

        self.m = m
        self.n = len(m)
        self.Q = Q
        self.r = [Fr.rnd() for _ in range(self.n)]
        self.R = [Q * r for r in self.r]

    def get_R(self):
        return self.R

    def get_encrypted(self, W):
        _1 = Fr()
        _1.setInt(1)
        k = [W * (_1/r) for r in self.r]
        c = [encrypt(m,k) for m,k in zip(self.m, k)]

        return c




class Receiver:
    def __init__(self, Q : G1, i : int) -> None:
        self.i = i
        self.Q = Q

    def get_W(self, R : list[G1]):
        alpha = Fr.rnd()
        assert self.i < len(R)
        W = R[self.i] * alpha

        self.ki = Q*alpha
        return W

    def decrypt(self, c : list[str]):
        return decrypt(c[self.i], self.ki)


Q = G1().hashAndMapTo(b'test')

m = [f"message {i}" for i in range(100)]
i = 15
sender = Sender(Q, m)
receiver = Receiver(Q, i)

R = sender.get_R()
W = receiver.get_W(R)
e = sender.get_encrypted(W)
mc = receiver.decrypt(e)

assert m[i] == mc, f'{m[i].encode()}; {mc.encode()};'
print(f'{m[i]=}; {mc=};')




