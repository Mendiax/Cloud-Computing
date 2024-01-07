from routes.encoding_utils import *
from protocols.protocol_oce import OCEUser
from protocols.protocol_one_of_two import OneOf2User

from globals import *

def oce(url):
    _CLIENT_IDX = 0
    _PROTOCOL_NAME = Protocols.OCE.value
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
    no_args = int(resp_data["payload"]["no_args"])
    num_of_messages = len(tmp_ciphertexts)
    assert _CLIENT_IDX < num_of_messages
    init_dic['session_token'] = token

    main_ciphertext = bytes.fromhex(tmp_ciphertexts[_CLIENT_IDX])
    print(main_ciphertext.hex())
    tmp_ciphertexts = []
    oce_user = OCEUser(_CLIENT_IDX, num_of_messages)

    # one of two part

    for key_idx in range(no_args):
        tmp_client_idx = oce_user.idx_bits_arr[key_idx]
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
        oce_user.add_key(key_idx, key)
        print(key_idx, key.hex())
    resp = oce_user.decrypt(main_ciphertext)
    print(f"MSG: {resp}")
    val = int.from_bytes(resp, 'big')
    print(f"MSG: {val}")