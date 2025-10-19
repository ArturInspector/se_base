from flask_socketio import Namespace, join_room
from flask import request
import traceback


class ClientSocket(Namespace):
    def on_connect(self):
        print('connect | {}'.format(request.sid))

    def on_subscribe(self, data):
        try:
            token = data.get('token', None)
            if token is not None:
                join_room(token)
                print('room added in {}'.format(token))
        except:
            print(traceback.format_exc())

    def on_disconnect(self):
        print('disconnected | {}'.format(request.sid))