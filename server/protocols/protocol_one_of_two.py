from mcl import *
from .protocols_utils import *

_SEC_PAR = b"test"
Q = G1.hashAndMapTo(_SEC_PAR)


class OneOf2Cloud():

    @staticmethod
    def keygen() -> tuple[Fr, G1]:
        _privkey = Fr.rnd()
        _pubkey = Q * _privkey
        return (_privkey, _pubkey)

    @staticmethod
    def gen_ciphertexts(privkey: Fr, pubkey: G1, messages: list[bytes], client_pubkey: G1) -> tuple[bytes]:
        k0 = client_pubkey*privkey
        k1 = (client_pubkey - pubkey)*privkey

        msg_len = get_max_len_of_elem_in_list(messages)

        hash0 = get_hash_concated_k_times(msg_len, k0.getStr())
        hash1 = get_hash_concated_k_times(msg_len, k1.getStr())

        e0 = encrypt(messages[0], hash0)
        e1 = encrypt(messages[1], hash1)

        return [e0, e1]


class OneOf2User():
    def __init__(self, idx: int):
        self.idx = idx

    def keygen(self, cloud_pubkey):
        _priv_key = Fr.rnd()
        self._enc_key_bytes = (cloud_pubkey*_priv_key).getStr()

        if self.idx == 0:
            pubkey = Q * _priv_key
        elif self.idx == 1:
            pubkey = cloud_pubkey + (Q * _priv_key)
        else:
            raise Exception("idx (choice) not in range")

        return pubkey

    def decrypt(self, c: list[bytes, bytes]):
        msg_len = get_max_len_of_elem_in_list(c)
        key_hash = get_hash_concated_k_times(msg_len, self._enc_key_bytes)

        return decrypt(c[self.idx], key_hash)
