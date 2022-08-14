
import requests
import time
import ast
import json

headers = {
    'X-CSRF': 'x',
    'Accept': 'application/json'
}
wifi_url_base = 'http://admin:5p4c3_P471@10.0.0.101/restapi/relay/outlets/'
wired_url_base = 'http://admin:1234@192.168.0.100/restapi/relay/outlets/'
