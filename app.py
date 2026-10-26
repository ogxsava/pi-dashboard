"""Pi status and internet speed dashboard.

Run:  python app.py [--port 8000] [--interval 30]
Then open http://<pi-address>:8000 in a browser.
"""
import argparse
import threading

from flask import Flask, jsonify, render_template

import db
import monitor

app = Flask(__name__)
_test_lock = threading.Lock()  # only one speed test at a time


def run_speed_test():
    """Run a speed test and store it. Returns None if one is already running."""
    if not _test_lock.acquire(blocking=False):
        return None
    try:
        result = monitor.speed_test()
        db.save(result)
        return result
    finally:
        _test_lock.release()


def background_tests(interval_minutes):
    stop = threading.Event()
    while not stop.is_set():
        run_speed_test()
        stop.wait(interval_minutes * 60)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    return jsonify(monitor.status())


@app.route("/api/speedtests")
def api_speedtests():
    return jsonify(db.recent())


@app.route("/api/speedtests/run", methods=["POST"])
def api_run():
    result = run_speed_test()
    if result is None:
        return jsonify({"error": "a speed test is already running"}), 409
    return jsonify(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--interval", type=int, default=30, help="minutes between speed tests")
    args = parser.parse_args()
    db.connect().close()  # make sure the table exists
    threading.Thread(target=background_tests, args=(args.interval,), daemon=True).start()
    app.run(host="0.0.0.0", port=args.port)
