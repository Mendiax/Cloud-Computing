import json
import mcl

def jstore(d):
    return json.dumps({ k: v.getStr().decode() if type(v) != bytes else v.hex() for k, v in d.items() })

def jload(d, j):
    j = json.loads(j)
    r = []
    for k, t in d.items():
        if t != bytes:
            v = t()
            v.setStr(j[k].encode())
        else:
            v = t.fromhex(j[k])
        r.append(v)
    return r

def mcl_to_str(mcl):
    return mcl.serialize().hex()

def mcl_from_str(mcl_str : str, cls):
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

def read_json_mcl(path : str):
    with open(path, 'r') as fd:
        return json.load(fd, cls=mclDecoder)



def write_json_mcl(path : str, dictionary):
    with open(path, 'w') as fd:
        json.dump(dictionary, fd, indent=2, cls=mclEncoder)