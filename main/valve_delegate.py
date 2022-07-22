import requests
import time
import stringutils
import json

arduino_base_url = "http://10.0.0.228" 


def set_valve_state(channel: int, state: bool):
    url=f'{arduino_base_url}/valves'
    params = {
        "channel" : channel,
        "value" : 1 if state else 0
    }
    return json.dumps(requests.post(url=url, params=params).json())

def set_all(state: bool):
    for i in range(16):
        set_valve_state(i, state)

def get_valve_state():
    url=f'{arduino_base_url}/status'
    response = requests.get(url=url).json()
    return json.dumps(response)
