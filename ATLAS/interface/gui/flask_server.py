import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from flask import Flask, jsonify, request
from flask_cors import CORS

from services.monitoring.system_awareness_v0_1.awareness import system_awareness
from interface.gui.gui_api import gui_api

app = Flask(__name__)
CORS(app)


@app.route("/api/live_state")
def live_state():
    return jsonify(gui_api.get_live_state())


@app.route("/api/today_usage")
def today_usage():
    return jsonify(gui_api.get_today_usage())


@app.route("/api/learning_progress")
def learning_progress():
    return jsonify(gui_api.get_learning_progress())


@app.route("/api/reminders")
def reminders():
    return jsonify(gui_api.get_reminders())


@app.route("/api/dismiss_reminder", methods=["POST"])
def dismiss_reminder():
    data = request.get_json()
    result = gui_api.dismiss_reminder(data.get("text"))
    return jsonify(result)


@app.route("/api/mute_proactive", methods=["POST"])
def mute_proactive():
    data = request.get_json()
    result = gui_api.mute_proactive(data.get("minutes"))
    return jsonify(result)


@app.route("/api/mute_status")
def mute_status():
    return jsonify(gui_api.get_mute_status())


@app.route("/api/conversation_log")
def conversation_log():
    return jsonify(gui_api.get_conversation_log())


@app.route("/api/last_notification")
def last_notification():
    result = gui_api.get_last_notification()
    return jsonify(result)


@app.route("/api/clear_conversation", methods=["POST"])
def clear_conversation():
    return jsonify(gui_api.clear_conversation_with_extraction())


@app.route("/api/extracted_facts")
def extracted_facts():
    return jsonify(gui_api.get_extracted_facts())


def run_server():
    system_awareness.start()
    app.run(host="127.0.0.1", port=7437, debug=False, use_reloader=False)


if __name__ == "__main__":
    run_server()
