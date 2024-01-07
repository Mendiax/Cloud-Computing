from mcl import *
from .protocols_utils import *
from secrets import SystemRandom

_SEC_PAR = b"test"
Q = G1.hashAndMapTo(_SEC_PAR)


class OCECloud():

    def __init__(self, func, no_arg : int):
        self.xy : list[tuple[list[int], int]] = [
            (x, func(*x)) for x in self.__binary_generator(no_arg)
        ]
        print(self.xy)
        self._rand_gen = SystemRandom()
        self.no_arg=no_arg
        self.L = 1
        self.key_pairs = self.gen_key_pairs()


    def __binary_generator(self, args_no):
        for i in range(2 ** args_no):
            binary_representation = bin(i)[2:].zfill(args_no)
            yield [int(x) for x in binary_representation]

    def gen_key_pairs(self) -> list[tuple[bytes, bytes]]:
        key_pairs = [(self._rand_gen.randbytes(self.L),
                           self._rand_gen.randbytes(self.L))
                          for _ in range(self.no_arg)]
        return key_pairs

    def gen_ciphertexts(self) -> list[bytes]:
        return [self._encrypt_one_msg(idx) for idx in range(len(self.xy))]

    def _encrypt_one_msg(self, msg_idx: int) -> bytes:
        result = self.xy[msg_idx][1].to_bytes(1, byteorder='big')
        for i,j in enumerate(self.xy[msg_idx][0]):
            _key = self.key_pairs[i][j]
            if msg_idx == 3:
                print(_key.hex())
            result = encrypt(result, _key)
        return result


class OCEUser():
    def __init__(self, idx: int, no_of_msgs: int) -> None:
        self.idx = idx
        self.no_of_msgs = no_of_msgs
        self.bitlength = int.bit_length(no_of_msgs-1)
        self.keys = [bytes(b'')] * self.bitlength
        self.idx_bits_arr = [get_ith_bit(self.idx, i)
                             for i in range(self.bitlength)]
        self.idx_bits_arr.reverse()
        print(self.bitlength, self.idx_bits_arr)

    def add_key(self, key_idx, key: bytes):
        self.keys[key_idx] = key

    def decrypt(self, ciphertext: bytes):
        result = ciphertext
        print(self.keys)
        for _key in self.keys:
            result = decrypt(result, _key)

        return result