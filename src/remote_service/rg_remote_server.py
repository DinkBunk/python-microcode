import string
import rg_settings
import json
import src.views.delegate.pump_delegate as pump_delegate

from types import SimpleNamespace
from flask import Flask, render_template, request

currentStatus: rg_settings = None
updatedRelayState: string = "0000000000000000"

remote_server = Flask(__name__)

@remote_server.route("/", methods=['GET'])
def dashboard():
    return render_template('rg_index.html', currentStatus)


@remote_server.route("/status", methods=['GET'])
def getStatus():
    return currentStatus

@remote_server.route("/status", methods=['POST'])
def postStatus():
    currentStatus = json.loads(request.json, object_hook=lambda d: SimpleNamespace(**d))
    return updatedRelayState

@remote_server.route("/relayState", methods='POST')
def postRelayState():
    updatedRelayState = request.json["relayState"]
    return updatedRelayState

remote_server.run(debug=True, host="0.0.0.0")
