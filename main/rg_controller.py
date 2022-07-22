from http.server import BaseHTTPRequestHandler, HTTPServer
from flask import Flask, render_template, request
import json
import time
import logging
import pump_delegate
import valve_delegate
import routines
import rg_flask_ui
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()


def lights_on():
    pump_delegate.set_pump_state(7, True)
    pump_delegate.set_pump_state(4, True)

def lights_off():
    pump_delegate.set_pump_state(7, False)
    pump_delegate.set_pump_state(4, False)

def feather_stack_pump() :
    pump_delegate.set_pump_state(2, True)
    time.sleep(10)
    pump_delegate.set_pump_state(2, False)

def short_cycle_drainage() :
    pump_delegate.set_pump_state(3, True)
    time.sleep(10)
    pump_delegate.set_pump_state(3, False)

def long_cycle_drainage() :
    pump_delegate.set_pump_state(3, True)
    time.sleep(120)
    pump_delegate.set_pump_state(3, False)

scheduler.add_job(lights_on, 'cron', hour=7)
scheduler.add_job(lights_off, 'cron', hour=23)
scheduler.add_job(feather_stack_pump, 'cron', minute=50)
scheduler.add_job(short_cycle_drainage, 'cron', minute=51)
scheduler.add_job(long_cycle_drainage, 'cron', hour=23)

scheduler.start()

app = Flask(__name__)


def toggle_valve(channel: int):
    if (valve_delegate.get_valve_state(channel)):
        valve_delegate.set_valve_state(channel, False)
    else:
        valve_delegate.set_valve_state(channel, True)

@app.route('/valves', methods=['POST']) 
def valve():
    args = request.get_json(force=True)
    channel = int(args["channel"])
    state = bool(int(args["state"]))
    if channel != 'all':
        valve_delegate.set_valve_state(channel, state)
    else :
        valve_delegate.set_all(state)

@app.route('/pumps', methods=['POST'])
def pump():
    args = request.get_json(force=True)
    channel = int(args["channel"])
    state = bool(int(args["state"]))
    pump_delegate.set_pump_state(channel, state)

@app.route('/pumps', methods=['GET'])
def pump_status():
    response = app.response_class(
        response=json.dumps(pump_delegate.get_all_states()),
        status=200,
        mimetype='application/json')
    return response

@app.route('/valves', methods=['GET'])
def valve_status():
    response = app.response_class(
        response=json.dumps(valve_delegate.get_all_states()),
        status=200,
        mimetype='application/json')
    return response

@app.route('/', methods=['GET', 'POST'])
def index() :
    if (request.method == 'POST'):
        if (request.form["toggle_button"] == "valve_1_on"):
            data = valve_delegate.set_valve_state(0, True)
            return render_template("index.html", jsonfile=json.dumps(data))

        if (request.form["toggle_button"] == "valve_2_on"):
            data = valve_delegate.set_valve_state(1, True)
            return render_template("index.html", jsonfile=json.dumps(data))

        if (request.form["toggle_button"] == "valve_3_on"):
            data = valve_delegate.set_valve_state(2, True)
            return render_template("index.html", jsonfile=json.dumps(data))

        if (request.form["toggle_button"] == "valve_4_on"):
            data = valve_delegate.set_valve_state(3, True)
            return render_template("index.html", jsonfile=json.dumps(data))

        if (request.form["toggle_button"] == "valve_5_on"):
            data = valve_delegate.set_valve_state(4, True)
            return render_template("index.html", jsonfile=json.dumps(data))

        if (request.form["toggle_button"] == "valve_6_on"):
            data = valve_delegate.set_valve_state(5, True)
            return render_template("index.html", jsonfile=json.dumps(data))

        if (request.form["toggle_button"] == "valve_7_on"):
            data = valve_delegate.set_valve_state(6, True)
            return render_template("index.html", jsonfile=json.dumps(data))

        if (request.form["toggle_button"] == "valve_8_on"):
            data = valve_delegate.set_valve_state(7, True)
            return render_template("index.html", jsonfile=json.dumps(data))

        if (request.form["toggle_button"] == "valve_9_on"):
            data = valve_delegate.set_valve_state(8, True)
            return render_template("index.html", jsonfile=json.dumps(data))

        if (request.form["toggle_button"] == "valve_10_on"):
            data = valve_delegate.set_valve_state(9, True)
            return render_template("index.html", jsonfile=json.dumps(data))

        if (request.form["toggle_button"] == "valve_11_on"):
            data = valve_delegate.set_valve_state(10, True)
            return render_template("index.html", jsonfile=json.dumps(data))

        if (request.form["toggle_button"] == "valve_12_on"):
            data = valve_delegate.set_valve_state(11, True)
            return render_template("index.html", jsonfile=json.dumps(data))

        if (request.form["toggle_button"] == "valve_13_on"):
            data = valve_delegate.set_valve_state(12, True)
            return render_template("index.html", jsonfile=json.dumps(data))

        if (request.form["toggle_button"] == "valve_14_on"):
            data = valve_delegate.set_valve_state(13, True)
            return render_template("index.html", jsonfile=json.dumps(data))

        if (request.form["toggle_button"] == "valve_15_on"):
            data = valve_delegate.set_valve_state(14, True)
            return render_template("index.html", jsonfile=json.dumps(data))

        if (request.form["toggle_button"] == "valve_16_on"):
            data = valve_delegate.set_valve_state(15, True)
            return render_template("index.html", jsonfile=json.dumps(data))

        if (request.form["toggle_button"] == "valve_1_off"):
            data = valve_delegate.set_valve_state(0, False)
            return render_template("index.html", jsonfile=json.dumps(data))

        if (request.form["toggle_button"] == "valve_2_off"):
            data = valve_delegate.set_valve_state(1, False)
            return render_template("index.html", jsonfile=json.dumps(data))

        if (request.form["toggle_button"] == "valve_3_off"):
            data = valve_delegate.set_valve_state(2, False)
            return render_template("index.html", jsonfile=json.dumps(data))

        if (request.form["toggle_button"] == "valve_4_off"):
            data = valve_delegate.set_valve_state(3, False)
            return render_template("index.html", jsonfile=json.dumps(data))

        if (request.form["toggle_button"] == "valve_5_off"):
            data = valve_delegate.set_valve_state(4, False)
            return render_template("index.html", jsonfile=json.dumps(data))

        if (request.form["toggle_button"] == "valve_6_off"):
            data = valve_delegate.set_valve_state(5, False)
            return render_template("index.html", jsonfile=json.dumps(data))

        if (request.form["toggle_button"] == "valve_7_off"):
            data = valve_delegate.set_valve_state(6, False)
            return render_template("index.html", jsonfile=json.dumps(data))

        if (request.form["toggle_button"] == "valve_8_off"):
            data = valve_delegate.set_valve_state(7, False)
            return render_template("index.html", jsonfile=json.dumps(data))

        if (request.form["toggle_button"] == "valve_9_off"):
            data = valve_delegate.set_valve_state(8, False)
            return render_template("index.html", jsonfile=json.dumps(data))

        if (request.form["toggle_button"] == "valve_10_off"):
            data = valve_delegate.set_valve_state(9, False)
            return render_template("index.html", jsonfile=json.dumps(data))

        if (request.form["toggle_button"] == "valve_11_off"):
            data = valve_delegate.set_valve_state(10, False)
            return render_template("index.html", jsonfile=json.dumps(data))

        if (request.form["toggle_button"] == "valve_12_off"):
            data = data = valve_delegate.set_valve_state(11, False)
            return render_template("index.html", jsonfile=json.dumps(data))
        if (request.form["toggle_button"] == "valve_13_off"):
            data = valve_delegate.set_valve_state(12, False)
            return render_template("index.html", jsonfile=json.dumps(data))

        if (request.form["toggle_button"] == "valve_14_off"):
            data = valve_delegate.set_valve_state(13, False)
            return render_template("index.html", jsonfile=json.dumps(data))

        if (request.form["toggle_button"] == "valve_15_off"):
            data = valve_delegate.set_valve_state(14, False)
            return render_template("index.html", jsonfile=json.dumps(data))

        if (request.form["toggle_button"] == "valve_16_off"):
            data = valve_delegate.set_valve_state(15, False)
            return render_template("index.html", jsonfile=json.dumps(data))

        if (request.form["toggle_button"] == "pump_1_on"):
            pump_delegate.set_pump_state(0, True)
            return render_template("index.html")
        if (request.form["toggle_button"] == "pump_2_on"):
            pump_delegate.set_pump_state(1, True)
            return render_template("index.html")
        if (request.form["toggle_button"] == "pump_3_on"):
            pump_delegate.set_pump_state(2, True)
            return render_template("index.html")
        if (request.form["toggle_button"] == "pump_4_on"):
            pump_delegate.set_pump_state(3, True)
            return render_template("index.html")
        if (request.form["toggle_button"] == "pump_5_on"):
            pump_delegate.set_pump_state(4, True)
            return render_template("index.html")
        if (request.form["toggle_button"] == "pump_6_on"):
            pump_delegate.set_pump_state(5, True)
            return render_template("index.html")
        if (request.form["toggle_button"] == "pump_7_on"):
            pump_delegate.set_pump_state(6, True)
            return render_template("index.html")
        if (request.form["toggle_button"] == "pump_8_on"):
            pump_delegate.set_pump_state(7, True)
            return render_template("index.html")
        if (request.form["toggle_button"] == "pump_1_off"):
            pump_delegate.set_pump_state(0, False)
            return render_template("index.html")
        if (request.form["toggle_button"] == "pump_2_off"):
            pump_delegate.set_pump_state(1, False)
            return render_template("index.html")
        if (request.form["toggle_button"] == "pump_3_off"):
            pump_delegate.set_pump_state(2, False)
            return render_template("index.html")
        if (request.form["toggle_button"] == "pump_4_off"):
            pump_delegate.set_pump_state(3, False)
            return render_template("index.html")
        if (request.form["toggle_button"] == "pump_5_off"):
            pump_delegate.set_pump_state(4, False)
            return render_template("index.html")
        if (request.form["toggle_button"] == "pump_6_off"):
            pump_delegate.set_pump_state(5, False)
            return render_template("index.html")
        if (request.form["toggle_button"] == "pump_7_off"):
            pump_delegate.set_pump_state(6, False)
            return render_template("index.html")
        if (request.form["toggle_button"] == "pump_8_off"):
            pump_delegate.set_pump_state(7, False)
            return render_template("index.html")
        if (request.form["status_button"] == "get_status"):
            return render_template("index.html", jsonfile=json.dumps(valve_delegate.get_valve_state().data))

    elif (request.method == "GET") :
        return render_template("index.html", jsonfile=valve_delegate.get_valve_state())



if __name__ == "__main__":
    app.run(port=8080, host='0.0.0.0')