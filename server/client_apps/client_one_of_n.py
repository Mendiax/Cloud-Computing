from routes.encoding_utils import *
from protocols.protocol_one_of_two import OneOf2User
from protocols.protocol_one_of_n import OneOfNUser
from globals import *


def one_of_n(url):
    _CLIENT_IDX = 8
    _PROTOCOL_NAME = Protocols.ONE_OF_N.value
    _PROTOCOL_ACTIONS = PROTOCOL_SPECS[_PROTOCOL_NAME]["actions"]
    init_dic = {
        "protocol_name": _PROTOCOL_NAME,
        "payload": {}
    }
    print(url, _PROTOCOL_NAME, init_dic, _PROTOCOL_ACTIONS[0])

    resp_data = post_stage(url, _PROTOCOL_NAME, init_dic,
                           _PROTOCOL_ACTIONS[0])
    token = resp_data["session_token"]
    tmp_ciphertexts = resp_data["payload"]["ciphertexts"]
    num_of_messages = len(tmp_ciphertexts)
    assert _CLIENT_IDX < num_of_messages
    init_dic['session_token'] = token

    main_ciphertext = bytes.fromhex(tmp_ciphertexts[_CLIENT_IDX])
    tmp_ciphertexts = []
    one_of_n_user = OneOfNUser(_CLIENT_IDX, num_of_messages)

    # one of two part

    for key_idx in range(one_of_n_user.bitlength):
        tmp_client_idx = one_of_n_user.idx_bits_arr[key_idx]
        one_of_two_user = OneOf2User(tmp_client_idx)
        resp_data = post_stage(url, _PROTOCOL_NAME, init_dic,
                               _PROTOCOL_ACTIONS[1])
        big_a = mcl_from_str(resp_data["payload"]["A"], mcl.G1)
        big_b = one_of_two_user.keygen(big_a)
        one_of_two_payload = {
            "protocol_name": _PROTOCOL_NAME,
            "payload": {
                "B": mcl_to_str(big_b),
                "key_idx": key_idx,
            },
            "session_token": token,
        }

        resp_data = post_stage(
            url, _PROTOCOL_NAME, one_of_two_payload, _PROTOCOL_ACTIONS[2])

        one_of_two_ciphertexts = [bytes.fromhex(
            cip) for cip in resp_data["payload"]['ciphertexts']]

        key = one_of_two_user.decrypt(one_of_two_ciphertexts)
        one_of_n_user.add_key(key_idx, key)

    print(f"MSG: {one_of_n_user.decrypt(main_ciphertext)}")
