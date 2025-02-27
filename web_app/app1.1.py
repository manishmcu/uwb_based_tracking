import time
import requests
import json
from flask import Flask, render_template, jsonify
import webbrowser
from threading import Timer

app = Flask(__name__)

ROBOT_IP = "192.168.1.87"  # Change this to your robot's IP
MOVE_URL = f"http://{ROBOT_IP}:8090/chassis/moves"
CANCEL_MOVE = f"http://{ROBOT_IP}:8090/chassis/moves/current"
OVERLAY_URL = "http://192.168.1.34/get_position"  # Update with actual overlay URL
PAYLOAD_FILE = "payload.json"

is_moving = False
is_tracking = False


def fetch_position_data():
    """Fetch the position data from the overlay link."""
    try:
        response = requests.get(OVERLAY_URL, timeout=2)
        if response.status_code == 200:
            data = response.text
            print(f"Received Position Data: {data}")

            if "Tag Position:" in data:
                lines = data.split("\n")
                for line in lines:
                    if line.startswith("Tag Position:"):
                        position_data = line.split(":")[1].strip()
                        tag_x, tag_y = map(float, position_data[1:-1].split(","))
                        tag_y = -tag_y
                        tag_x = -tag_x
                        return tag_x, tag_y
            else:
                print("Invalid position data format.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
    return None, None


def update_payload_file(tag_x, tag_y):
    """Update the payload.json file with new coordinates."""
    try:
        payload = {
            "target_x": tag_x,
            "target_y": tag_y
        }

        with open(PAYLOAD_FILE, 'w') as file:
            json.dump(payload, file, indent=4)

        print(f"Payload updated: {payload}")
        return payload
    except Exception as e:
        print(f"Error updating payload file: {e}")
        return None


def tracking_task():
    global is_tracking, is_moving

    while is_tracking:
        time.sleep(1)  # Check every second
        tag_x, tag_y = fetch_position_data()
        if tag_x is None or tag_y is None:
            continue

        # Check distance > 0.5m
        if tag_x ** 2 + tag_y ** 2 > 0.25:
            if not is_moving:
                payload = update_payload_file(tag_x, tag_y)
                if payload:
                    try:
                        response = requests.post(MOVE_URL, json=payload)
                        if response.status_code == 200:
                            is_moving = True
                            print("Move request sent during tracking.")
                    except requests.exceptions.RequestException as e:
                        print(f"Error sending move request during tracking: {e}")


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/start_tracking', methods=['POST'])
def start_tracking():
    global is_tracking
    print("Start Tracking button pressed!")
    if not is_tracking:
        is_tracking = True
        Timer(0, tracking_task).start()
        return jsonify({"status": "success", "message": "Tracking started."})
    else:
        return jsonify({"status": "error", "message": "Already tracking."})


@app.route('/stop_tracking', methods=['POST'])
def stop_tracking():
    global is_tracking, is_moving
    print("Stop Tracking button pressed!")
    is_tracking = False
    is_moving = False

    try:
        response = requests.patch(CANCEL_MOVE, json={"state": "cancelled"})
        if response.status_code == 200:
            print("Move canceled during stop tracking.")
            return jsonify({"status": "success", "message": "Tracking stopped."})
    except requests.exceptions.RequestException as e:
        print(f"Error during stop tracking: {e}")
    return jsonify({"status": "error", "message": "Failed to stop tracking."})


@app.route('/call', methods=['POST'])
def call():
    global is_moving
    print("Call button pressed!")
    if not is_moving:
        tag_x, tag_y = fetch_position_data()
        if tag_x is None or tag_y is None:
            return jsonify({"status": "error", "message": "Failed to fetch position data."}), 400

        payload = update_payload_file(tag_x, tag_y)
        if not payload:
            return jsonify({"status": "error", "message": "Failed to update payload."}), 500

        try:
            response = requests.post(MOVE_URL, json=payload)
            if response.status_code == 200:
                is_moving = True
                print("Move request sent successfully.")
                return jsonify({"status": "success", "message": "Robot is moving."})
        except requests.exceptions.RequestException as e:
            print(f"Error during move request: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    else:
        return jsonify({"status": "error", "message": "Robot is already moving."}), 400


@app.route('/cancel', methods=['POST'])
def cancel():
    global is_moving
    print("Cancel button pressed!")
    try:
        response = requests.patch(CANCEL_MOVE, json={"state": "cancelled"})
        if response.status_code == 200:
            is_moving = False
            return jsonify({"status": "success", "message": "Move canceled."})
    except requests.exceptions.RequestException as e:
        print(f"Error during cancel request: {e}")
    return jsonify({"status": "error", "message": "Failed to cancel move."})


def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")


if __name__ == "__main__":
    Timer(1, open_browser).start()
    app.run(debug=True, host='0.0.0.0', port=5000)
