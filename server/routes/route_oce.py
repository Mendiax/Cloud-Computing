from flask import request, current_app, jsonify, abort
from db_model import db
from db_model import Session, Keys
from protocols import OCECloud, OCEUser
from routes.route_one_of_two import one_of_two_send_A, one_of_two_send_ciphertexts
from routes.encoding_utils import *
from pprint import pformat
from globals import *


PROTOCOL_NAME = Protocols.OCE.value
PROTOCOL_ACTIONS = PROTOCOL_SPECS[PROTOCOL_NAME]["actions"]
routes = []

_NUM_OF_ARGS = 4
def get_example_func(x,y,u,v):
    return (x & y) | (u ^ v)
_FUNC = get_example_func


def oce_send_ciphertexts():
    print('here')
    if request.data and type(request.data) is dict:
        data = request.data
    else:
        data = request.json
    if data.get("protocol_name") == PROTOCOL_NAME:
        payload = data.get("payload")
        current_app.logger.info(
            f"[one_of_n] Received payload:\n{pformat(payload)}")
        token = generate_token()
        cloud = OCECloud(_FUNC, _NUM_OF_ARGS)
        key_pairs = [(key0.hex(), key1.hex())
                     for key0, key1 in cloud.key_pairs]

        ciphertexts = [cipher.hex() for cipher in cloud.gen_ciphertexts()]
        # assert cloud.no_arg == len(ciphertexts)

        print(key_pairs)
        print(ciphertexts)


        to_insert = [Keys(session_token=token, key_idx=i, key0_val=_key0, key1_val=_key1)
                     for i, (_key0, _key1) in enumerate(key_pairs)]

        try:
            db.session.add_all(to_insert)
            db.session.commit()
        except:
            db.create_all()
            db.session.rollback()
            db.session.add_all(to_insert)
            db.session.commit()

        response = {
            "session_token": token,
            "payload": {
                "ciphertexts": ciphertexts,
                "no_args" : _NUM_OF_ARGS
            },
        }

        return jsonify(response)


def _messages_provider_func(data):
    token = data.get("session_token")
    key_idx = data.get("payload").get("key_idx")
    session_data = Session.query.filter_by(session_token=token).first()
    if session_data == None:
        abort(404, "Session not found")
    key_from_db = Keys.query.filter_by(
        session_token=token, key_idx=key_idx).first()
    messages = [bytes.fromhex(key_from_db.key0_val),
                bytes.fromhex(key_from_db.key1_val)]

    try:
        db.session.delete(key_from_db)
        db.session.commit()
    except:
        current_app.logger.info(
            f"[one_of_n] cannot delete key\n{pformat(key_from_db)}")

    return messages


routes.append(dict(
    rule=f'/{PROTOCOL_NAME}/{PROTOCOL_ACTIONS[0]}',
    view_func=oce_send_ciphertexts,
    options=dict(methods=['POST'])))


routes.append(dict(
    rule=f'/{PROTOCOL_NAME}/{PROTOCOL_ACTIONS[1]}',
    view_func=one_of_two_send_A(PROTOCOL_NAME),
    options=dict(methods=['POST']),
    endpoint="oce_get_A"))


routes.append(dict(
    rule=f'/{PROTOCOL_NAME}/{PROTOCOL_ACTIONS[2]}',
    view_func=one_of_two_send_ciphertexts(
        _messages_provider_func, PROTOCOL_NAME),
    options=dict(methods=['POST']),
    endpoint="oce_get_two_ciphertexts"))

