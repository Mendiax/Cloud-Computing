from db_model import Session, db
from flask import request, current_app, jsonify, abort
from protocols import OneOf2Cloud
from routes.encoding_utils import *
from .encoding_utils import gen_example_messages
from pprint import pformat
from globals import *

PROTOCOL_NAME = Protocols.ONE_OF_TWO.value
PROTOCOL_ACTIONS = PROTOCOL_SPECS[PROTOCOL_NAME]["actions"]
routes = []


def _message_provider_func(data):
    return gen_example_messages(2)


def one_of_two_send_A(protocol_name):
    def send_A():
        if request.data and type(request.data) is dict:
            data = request.data
        else:
            data = request.json
        if data.get("protocol_name") == protocol_name:
            payload = data.get("payload")
            current_app.logger.info(
                f"[one_of_two] Received payload:\n{pformat(payload)}")
            a, big_a = OneOf2Cloud.keygen()
            if protocol_name == PROTOCOL_NAME:
                token = generate_token()
            elif "session_token" not in data:
                abort(404, "Session token not found")
            else:
                token = data.get("session_token")

            db_data = {
                "a": mcl_to_str(a),
                "A": mcl_to_str(big_a)
            }
            try:
                db.session.add(Session(session_token=token, payload=db_data))
                db.session.commit()
            except:
                db.create_all()
                db.session.rollback()
                current_app.logger.info(f"Bad session_token {token=}")
            response = {
                "session_token": token,
                "payload": {
                    "A": mcl_to_str(big_a)
                }
            }
            current_app.logger.info(
                f"[{protocol_name}] Sent response A : {big_a}")
            return jsonify(response)

    return send_A


def one_of_two_send_ciphertexts(messages_provider, protocol_name):
    def send_ciphertexts():
        if request.data and type(request.data) is dict:
            data = request.data
        else:
            data = request.json
        if data.get("protocol_name") == protocol_name:
            payload = data.get("payload")
            big_b = mcl_from_str(payload.get("B"), mcl.G1)
            token = data.get("session_token")
            current_app.logger.info(
                f"[one_of_two] Received B:\n{pformat(big_b)}")
            session_data = Session.query.filter_by(session_token=token).first()
            a = mcl_from_str(session_data.payload.get("a"), mcl.Fr)
            big_a = mcl_from_str(session_data.payload.get("A"), mcl.G1)
            # Use the provided function to get messages
            messages = messages_provider(data)
            ciphertexts = OneOf2Cloud.gen_ciphertexts(
                a, big_a, messages, big_b)

            response = {
                "payload": {
                    "ciphertexts": [cip.hex() for cip in ciphertexts]
                }
            }

            try:
                db.session.delete(session_data)
                db.session.commit()
            except:
                db.create_all()
                db.session.rollback()
                db.session.delete(session_data)
                db.session.commit()

            return jsonify(response)

    return send_ciphertexts


routes.append(dict(
    rule=f'/{PROTOCOL_NAME}/{PROTOCOL_ACTIONS[0]}',
    view_func=one_of_two_send_A(PROTOCOL_NAME),
    options=dict(methods=['POST']),
    endpoint="one_of_two_get_A"))

routes.append(dict(
    rule=f'/{PROTOCOL_NAME}/{PROTOCOL_ACTIONS[1]}',
    view_func=one_of_two_send_ciphertexts(
        _message_provider_func, PROTOCOL_NAME),
    options=dict(methods=['POST']),
    endpoint="one_of_two_get_ciphertexts"))
