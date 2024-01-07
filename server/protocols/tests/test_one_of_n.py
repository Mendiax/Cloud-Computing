from protocols import OneOfNCloud, OneOfNUser
from .test_one_of_two import one_of_two_run_once
from routes.encoding_utils import gen_example_messages


def test_one_of_n_run_simulation():
    _NUM_OF_MESSAGES = 100
    messages = gen_example_messages(_NUM_OF_MESSAGES)
    cloud = OneOfNCloud(messages)
    for user_idx in range(cloud.num_of_messages):
        user = OneOfNUser(user_idx, cloud.num_of_messages)
        ciphertexts = cloud.gen_ciphertexts()
        for idx, (key0, key1) in enumerate(cloud.key_pairs):
            bit_val = user.idx_bits_arr[idx]
            key = one_of_two_run_once([key0, key1], bit_val)
            user.add_key(idx, key)

        assert user.decrypt(ciphertexts[user_idx]) == cloud.messages[user_idx]
