import requests
from uuid import uuid4
import json
import mcl


def generate_token():
    return str(uuid4())


def mcl_to_str(mcl):
    return mcl.serialize().hex()


def mcl_from_str(mcl_str: str, cls):
    mcl = cls()
    mcl.deserialize(bytes.fromhex(mcl_str))
    return mcl


class mclEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, mcl.Fr) or\
                isinstance(obj, mcl.G1) or\
                isinstance(obj, mcl.G2):
            return mcl_to_str(obj)
        return super().default(obj)


class mclDecoder(json.JSONDecoder):
    def decode(self, s):
        obj = super().decode(s)
        if isinstance(obj, str):
            try:
                return mcl_from_str(obj, mcl.Fr)
            except ValueError:
                try:
                    return mcl_from_str(obj, mcl.G1)
                except ValueError:
                    try:
                        return mcl_from_str(obj, mcl.G2)
                    except ValueError:
                        return obj
        return obj


def mcl_json_str_to_dic(input_json: str):
    return json.loads(input_json, cls=mclDecoder)


def mcl_dic_to_json_str(dic):
    return json.dumps(dic, indent=2, cls=mclEncoder)


def post_stage(url, protocol, dic, stage):
    res = requests.post(
        url=f'{url}/protocols/{protocol}/{stage}', json=dic)
    print(res)
    data = res.json()
    return data


def gen_example_messages(no_of_msgs):
    return [
        f"Hello from cloud = {i}".encode('ascii') for i in range(no_of_msgs)]
