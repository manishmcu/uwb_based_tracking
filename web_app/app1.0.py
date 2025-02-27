import time
import requests
import json
from flask import Flask, render_template, jsonify
import webbrowser
from threading import Timer

app = Flask(__name__)

# anchor_coor = {}
# dist_matrix = {}

# Robot and API configuration
ROBOT_IP = "192.168.1.87"  # Change this to your robot's IP
MOVE_URL = f"http://{ROBOT_IP}:8090/chassis/moves"
CANCEL_MOVE = f"http://{ROBOT_IP}:8090/chassis/moves/current"
OVERLAY_URL = "http://192.168.1.87/get_position"  # Update with actual overlay URL
PAYLOAD_FILE = "payload.json"

is_moving = False


def fetch_position_data():
    """Fetch the position data from the overlay link."""
    try:
        response = requests.get(OVERLAY_URL, timeout=2)
        if response.status_code == 200:
            data = response.text
            print(f"Received Position Data: {data}")

            # Parse the position data (extract Tag Position)
            if "Tag Position:" in data:
                lines = data.split("\n")
                for line in lines:
                    if line.startswith("Tag Position:"):
                        position_data = line.split(":")[1].strip()  # Extract (x, y) part
                        tag_x, tag_y = map(float, position_data[1:-1].split(","))
                        tag_y = - (tag_y)    # check the coordinate system, put Negetive_y if required
                        tag_x = - (tag_x)    # check the coordinate system, put Negetive_x if required
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


@app.route('/')
def home():
    return render_template('index.html')


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
            else:
                print(f"Failed to send move request. Status code: {response.status_code}")
                return jsonify({"status": "error", "message": "Failed to send move request."}), 400
        except requests.exceptions.RequestException as e:
            print(f"Error during move request: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    else:
        print("Call request ignored: Robot is already moving.")
        return jsonify({"status": "error", "message": "Robot is already moving."}), 400


@app.route('/cancel', methods=['POST'])
def cancel():
    global is_moving
    print("Cancel button pressed!")
    try:
        response = requests.patch(CANCEL_MOVE, json={"state": "cancelled"})
        if response.status_code == 200:
            is_moving = False
            print("Move cancelled successfully.")
            return jsonify({"status": "success", "message": "Move canceled."})
        else:
            print("Failed to cancel move.")
            return jsonify({"status": "error", "message": "Failed to cancel move."}), 400
    except requests.exceptions.RequestException as e:
        print(f"Error during cancel request: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")


if __name__ == "__main__":
    Timer(1, open_browser).start()
    app.run(debug=True, host='0.0.0.0', port=5000)
