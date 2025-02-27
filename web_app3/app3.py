from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import csv
import math
import requests
import json
from datetime import datetime

app = Flask(__name__)

# Directory for storing project files
BASE_DIR = "projects"
if not os.path.exists(BASE_DIR):
    os.mkdir(BASE_DIR)


# Helper: Format UNIX timestamp
@app.template_filter('datetimeformat')
def datetimeformat(value):
    """Format a UNIX timestamp into a human-readable string."""
    return datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')


# Helper: Calculate coordinates from range
def calculate_coordinates(anchor_id, distance):
    """Calculate the x, y coordinates based on the anchor's distance."""
    angle = (anchor_id - 1) * 45
    x = round(distance * math.cos(math.radians(angle)), 4)
    y = round(distance * math.sin(math.radians(angle)), 4)
    return x, y


# Helper: Save anchors to CSV
def save_anchors_to_csv(filepath, anchors):
    """Save the anchor data into a CSV file."""
    with open(filepath, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["A", "x", "y", "range"])
        writer.writeheader()
        for anchor in anchors:
            writer.writerow(anchor)


@app.route("/")
def home():
    """Render the home page."""
    return render_template("home.html")


@app.route("/new_project", methods=["GET", "POST"])
def new_project():
    """Create a new project with anchor data."""
    if request.method == "POST":
        project_id = request.form.get("project_id")
        project_path = os.path.join(BASE_DIR, project_id)

        if not os.path.exists(project_path):
            os.mkdir(project_path)

        csv_path = os.path.join(project_path, f"{project_id}.csv")

        # Get initial anchor distances
        distance_a1 = float(request.form.get("distance_a1"))
        distance_a2 = float(request.form.get("distance_a2"))
        a1 = {"A": "A1", "x": 0.0, "y": 0.0, "range": distance_a1}
        a2 = {"A": "A2", "x": distance_a2, "y": 0.0, "range": distance_a2}

        anchors = [a1, a2]

        # Process additional anchors dynamically
        anchor_index = 3
        while True:
            distance_a1_key = f"distance_a{anchor_index}_a1"
            distance_a2_key = f"distance_a{anchor_index}_a2"

            if distance_a1_key not in request.form or distance_a2_key not in request.form:
                break

            d1 = float(request.form.get(distance_a1_key))
            d2 = float(request.form.get(distance_a2_key))

            # Calculate x, y coordinates for the anchor
            x = (d1**2 - d2**2 + (a2["x"] - a1["x"])**2) / (2 * (a2["x"] - a1["x"]))
            y_squared = d1**2 - x**2
            y = math.sqrt(y_squared) if y_squared >= 0 else 0.0  # Handle edge cases

            anchors.append({
                "A": f"A{anchor_index}",
                "x": round(x, 4),
                "y": round(y, 4),
                "range": round(d1, 4),
            })

            anchor_index += 1

        # Save anchors to a CSV file
        save_anchors_to_csv(csv_path, anchors)

        # Render success page with a summary of saved anchors
        return render_template(
            "success.html",
            message=f"Project {project_id} created successfully!",
            anchors=anchors
        )

    return render_template("new_project.html")


@app.route("/edit_project", methods=["GET", "POST"])
def edit_project():
    """Edit an existing project."""
    if request.method == "POST":
        project_id = request.form.get("project_id")
        project_path = os.path.join(BASE_DIR, project_id)
        csv_path = os.path.join(project_path, f"{project_id}.csv")

        if not os.path.exists(csv_path):
            return render_template("error.html", message="The selected project does not exist.")

        return redirect(url_for("edit_specific_project", project_id=project_id))

    projects = [d for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d))]
    return render_template("edit_project.html", projects=projects)


@app.route("/edit_project/<project_id>", methods=["GET", "POST"])
def edit_specific_project(project_id):
    """Edit anchor data for a specific project."""
    project_path = os.path.join(BASE_DIR, project_id)
    csv_path = os.path.join(project_path, f"{project_id}.csv")

    if not os.path.exists(csv_path):
        return render_template("error.html", message="The selected project does not exist.")

    if request.method == "POST":
        anchors = []
        for i in range(len(request.form.getlist("x"))):
            anchors.append({
                "A": request.form.getlist("A")[i],
                "x": float(request.form.getlist("x")[i]),
                "y": float(request.form.getlist("y")[i]),
                "range": float(request.form.getlist("range")[i]),
            })
        save_anchors_to_csv(csv_path, anchors)
        return render_template("success.html", message=f"Project {project_id} updated successfully!")

    anchors = []
    with open(csv_path, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            anchors.append(row)

    return render_template("edit_specific_project.html", project_id=project_id, anchors=anchors)


@app.route("/get_ranges")
def get_ranges():
    """Fetch anchor range data from ESP32."""
    try:
        esp32_url = "http://192.168.1.34/get_ranges"  # Replace with ESP32 IP
        response = requests.get(esp32_url, timeout=5)
        return response.text, response.status_code, {"Content-Type": "text/plain"}
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to connect to ESP32", "details": str(e)}), 500


@app.route("/update", methods=["GET", "POST"])
def update():
    """Update anchor data on the ESP32."""
    projects = []
    for project_name in os.listdir(BASE_DIR):
        project_path = os.path.join(BASE_DIR, project_name)
        csv_path = os.path.join(project_path, f"{project_name}.csv")
        if os.path.exists(csv_path):
            modification_time = os.path.getmtime(csv_path)
            formatted_time = datetime.fromtimestamp(modification_time).strftime('%Y-%m-%d %H:%M:%S')
            projects.append({"name": project_name, "timestamp": formatted_time})

    if request.method == "POST":
        project_id = request.form.get("selected_project")
        if project_id:
            project_path = os.path.join(BASE_DIR, project_id)
            csv_path = os.path.join(project_path, f"{project_id}.csv")

            if os.path.exists(csv_path):
                with open(csv_path, newline="") as csvfile:
                    reader = csv.DictReader(csvfile)
                    anchors = [row for row in reader]

                anchor_data = {
                    "anchors": [
                        {
                            "A": anchor["A"],
                            "x": float(anchor["x"]),
                            "y": float(anchor["y"]),
                            "range": float(anchor["range"]),
                        }
                        for anchor in anchors
                    ]
                }

                try:
                    esp32_url = "http://192.168.1.34/save"  # Replace with ESP32 IP
                    headers = {"Content-Type": "application/json"}
                    response = requests.post(esp32_url, json=anchor_data, headers=headers)

                    if response.status_code == 200:
                        return render_template("update.html", projects=projects, message="Update successful!")
                    else:
                        return render_template("update.html", projects=projects, message="Failed to update ESP32.")
                except requests.exceptions.RequestException as e:
                    return render_template("error.html", message="Error communicating with ESP32.")

    return render_template("update.html", projects=projects)

@app.route("/live_distances")
def live_distances():
    """
    Fetch live distances from ESP32 and return as JSON.
    """
    try:
        esp32_url = "http://192.168.1.34/get_ranges"  # Replace with ESP32 IP
        response = requests.get(esp32_url, timeout=5)
        data = response.text.strip().split("\n")
        
        # Process the data returned from ESP32
        distances = {}
        for line in data:
            key, value = line.split(": ")
            # Remove any non-numeric characters (e.g., "m")
            numeric_value = ''.join(c for c in value if c.isdigit() or c == '.')
            distances[key] = float(numeric_value)

        return jsonify(distances)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to fetch distances", "details": str(e)}), 500
    except ValueError as e:
        return jsonify({"error": "Invalid data format from ESP32", "details": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
