import time
import requests
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, render_template, jsonify
import webbrowser
from threading import Timer

app = Flask(__name__)

# Robot configuration (update robot name here)
ROBOT_NAME = "8982410b042346i"
MOVE_URL = ""
CANCEL_MOVE = ""
OVERLAY_URL = "http://192.168.1.34/get_position"  # Update with actual overlay URL

is_moving = False
is_tracking = False
coordinate_type = "+"  # Can be "+" or "-" to control the coordinate sign

def get_ip_addresses():
    """Run nmap to detect live IP addresses in the network."""
    result = subprocess.run(["nmap", "-sn", "-T4", "-n", "192.168.1.0/24"], capture_output=True, text=True)
    ip_addresses = []
    for line in result.stdout.splitlines():
        if "Nmap scan report for" in line:
            parts = line.split()
            if len(parts) > 4 and parts[4].count('.') == 3:  # Check for IP format
                ip_addresses.append(parts[4])
    return ip_addresses

def check_if_robot(ip):
    """Check if an IP address belongs to the target robot."""
    url = f"http://{ip}:8090/device/info"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            device_data = response.json()
            if "device" in device_data:
                sn = device_data["device"].get("sn", "Unknown")
                if ROBOT_NAME in sn:
                    return ip, sn
    except requests.RequestException:
        return None, None  # If unable to connect or any error
    return None, None

def find_robot_ip():
    """Discover the robot's IP address based on its name."""
    ip_addresses = get_ip_addresses()
    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_ip = {executor.submit(check_if_robot, ip): ip for ip in ip_addresses}
        for future in as_completed(future_to_ip):
            ip, sn = future.result()
            if ip and sn:
                print(f"Robot found: {sn} at {ip}")
                return ip
    print("No robots found.")
    return None

# Fetch and set robot IP dynamically
ROBOT_IP = find_robot_ip()

if ROBOT_IP:
    MOVE_URL = f"http://{ROBOT_IP}:8090/chassis/moves"
    CANCEL_MOVE = f"http://{ROBOT_IP}:8090/chassis/moves/current"
    
    # Open browser after the robot IP is found
    # Timer(1, lambda: webbrowser.open_new("http://127.0.0.1:5000/")).start()
else:
    print("Unable to find the robot. Exiting.")
    exit(1)

def fetch_position_data():
    """Fetch position data from the overlay link."""
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
                        # Adjust coordinates based on the coordinate_type
                        if coordinate_type == "-":
                            tag_x = -tag_x
                            tag_y = -tag_y
                        return tag_x, tag_y
            else:
                print("Invalid position data format.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
    return None, None

def tracking_task():
    """Task to track the robot's position."""
    global is_tracking, is_moving
    while is_tracking:
        time.sleep(1)  # Check every second
        tag_x, tag_y = fetch_position_data()
        if tag_x is None or tag_y is None:
            continue
        if tag_x ** 2 + tag_y ** 2 > 0.25:
            if not is_moving:
                payload = {
                    "target_x": tag_x,
                    "target_y": tag_y
                }
                try:
                    response = requests.post(MOVE_URL, json=payload)
                    if response.status_code == 200:
                        is_moving = True
                        print("Move request sent during tracking.")
                    else:
                        print(f"Move request failed: {response.status_code}")
                except requests.exceptions.RequestException as e:
                    print(f"Error sending move request: {e}")

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
            print("Move canceled.")
            return jsonify({"status": "success", "message": "Tracking stopped."})
    except requests.exceptions.RequestException as e:
        print(f"Error during stop: {e}")
    return jsonify({"status": "error", "message": "Failed to stop tracking."})

@app.route('/call', methods=['POST'])
def call():
    global is_moving
    print("Call button pressed!")
    
    # If the robot is moving (from tracking or a previous call), don't allow a new move
    if is_moving:
        return jsonify({"status": "error", "message": "Robot is already moving."}), 400

    # Fetch position data
    tag_x, tag_y = fetch_position_data()
    if tag_x is None or tag_y is None:
        return jsonify({"status": "error", "message": "Failed to fetch position data."}), 400

    payload = {
    "target_x": tag_x,
    "target_y": tag_y
    }

    # Send the move request to the robot
    try:
        response = requests.post(MOVE_URL, json=payload)
        if response.status_code == 200:
            is_moving = True  # Set the robot as moving once the request is successful
            print("Move request sent successfully.")
            return jsonify({"status": "success", "message": "Robot is moving."})
        else:
            return jsonify({"status": "error", "message": "Failed to send move request."}), 500
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

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
        print(f"Error during cancel: {e}")
    return jsonify({"status": "error", "message": "Failed to cancel move."})

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
