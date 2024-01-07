from routes.encoding_utils import *
from protocols.protocol_one_of_two import OneOf2User
from globals import *


def one_of_two(url):
    _CLIENT_IDX = 1
    _PROTOCOL_NAME = Protocols.ONE_OF_TWO.value
    _PROTOCOL_ACTIONS = PROTOCOL_SPECS[_PROTOCOL_NAME]["actions"]

    init_dic = {
        "protocol_name": _PROTOCOL_NAME,
        "payload": {}
    }
    resp_data = post_stage(url, _PROTOCOL_NAME, init_dic, _PROTOCOL_ACTIONS[0])
    token = resp_data.get("session_token")
    big_a = mcl_from_str(resp_data.get("payload").get("A"), mcl.G1)
    user = OneOf2User(_CLIENT_IDX)

    init_dic['session_token'] = token
    init_dic['payload']['B'] = mcl_to_str(user.keygen(big_a))

    resp_data = post_stage(url, _PROTOCOL_NAME, init_dic, _PROTOCOL_ACTIONS[1])
    ciphertext_in_hex: list[str] = resp_data.get("payload").get("ciphertexts")
    ciphertexts_in_bytes = [bytes.fromhex(
        hex_string) for hex_string in ciphertext_in_hex]

    print(f"MSG: {user.decrypt(ciphertexts_in_bytes)}")
