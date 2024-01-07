from hashlib import sha3_512


def _xor_bytes(ba1: bytes, ba2: bytes):
    return bytes([_a ^ _b for _a, _b in zip(ba1, ba2)])


def encrypt(message_bytes: bytes, key_bytes: bytes):
    assert len(message_bytes) <= len(
        key_bytes), f'{len(message_bytes)=}'

    message_aligned = message_bytes.ljust(len(key_bytes), b"\x00")
    return _xor_bytes(message_aligned, key_bytes)


def decrypt(ciphertext_bytes: bytes, key_bytes: bytes):
    assert len(ciphertext_bytes) <= len(key_bytes), f'{len(ciphertext_bytes)=} {len(key_bytes)=}'
    return _xor_bytes(ciphertext_bytes, key_bytes).rstrip(b"\x00")


def get_ith_bit(val: int, i: int):
    if i < 0:
        raise ValueError("Index i must be non-negative")

    # Right shift val by i, then check the LSB
    return (val >> i) & 1


def get_max_len_of_elem_in_list(_list: list[bytes]) -> int:
    return len(max(_list, key=len))


_HASH_FUNC = sha3_512
HASH_LEN = _HASH_FUNC().digest_size


def get_hash(msg: bytes):
    return _HASH_FUNC(msg).digest()


def _get_number_of_blocks(msg_len: int) -> int:
    hash_len = HASH_LEN
    diff = msg_len - hash_len
    num_of_blocks = 1
    if diff > 0:
        num_of_blocks += (diff + hash_len)//hash_len
    return num_of_blocks


def get_hash_concated_k_times(msg_len: int, key: bytes):
    num_of_blocks = _get_number_of_blocks(msg_len)
    int_len = num_of_blocks.bit_length()
    return b''.join(get_hash(key + idx.to_bytes(int_len, 'little'))
                    for idx in range(num_of_blocks))
