import requests
import time
import ast
import json
import stringutils


headers = {
    'X-CSRF': 'x',
    'Accept': 'application/json'
}
wifi_url_base = 'http://admin:5p4c3_P471@10.0.0.101/restapi/relay/outlets/'
wired_url_base = 'http://admin:1234@192.168.0.100/restapi/relay/outlets/'

def parse_state_response(state_string: str) -> list:
    return json.loads(state_string)

def convert_readable_state(state: bool) ->str :
    if (state) :
        return "true"
    else:
        return "false"

def get_pump_state(channel_expr: str) -> list: 
    url = wifi_url_base + f'={channel_expr}/state'
    return parse_state_response(requests.get(url).text)

def get_all_states() :
    url = wifi_url_base + f'all;/state'
    return parse_state_response(requests.get(url).text)

def pump_for_duration(pumpchannel: int, duration: int):
    set_pump_state(pumpchannel, True)
    time.sleep(duration)
    set_pump_state(pumpchannel, False)

def set_pump_state(channel_expr: str, state: bool) :
    url = wifi_url_base + f'={channel_expr}/state'
    requests.put(headers=headers, url=url, data=convert_readable_state(state))

def feather_pump_outlet(channel: str, on_interval_seconds: int, off_interval_seconds: int, repeat: int) :
    while (repeat > 0) :
        set_pump_state(channel, True)
        time.sleep(on_interval_seconds)
        set_pump_state(channel, False)
        time.sleep(off_interval_seconds)
        repeat -= 1  






