from protocols import OneOf2Cloud, OneOf2User
from routes.encoding_utils import gen_example_messages

def test_one_of_two_run_simulation():
    messages = gen_example_messages(2)
    for idx in range(0, 2):
        decrypted = one_of_two_run_once(messages, idx)
        assert decrypted == messages[idx]
    print("PASSED")


def one_of_two_run_once(messages, idx: int)-> bytes:
    user = OneOf2User(idx)
    cloud = OneOf2Cloud()
    a, big_a = cloud.keygen()
    big_b = user.keygen(big_a)
    c = cloud.gen_ciphertexts(a, big_a, messages, big_b)
    return user.decrypt(c)
