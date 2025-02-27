from flask import Flask, render_template, request, redirect, url_for
import os
import csv
import math
import requests
import json

app = Flask(__name__)

# Directory for storing project files
BASE_DIR = "projects"
if not os.path.exists(BASE_DIR):
    os.mkdir(BASE_DIR)

from datetime import datetime

# Define a custom Jinja2 filter
@app.template_filter('datetimeformat')
def datetimeformat(value):
    """Format a UNIX timestamp into a human-readable string."""
    return datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')

# Helper to calculate coordinates from range
def calculate_coordinates(anchor_id, distance):
    angle = (anchor_id - 1) * 45
    x = round(distance * math.cos(math.radians(angle)), 4)
    y = round(distance * math.sin(math.radians(angle)), 4)
    return x, y

# Helper to save anchors to CSV
def save_anchors_to_csv(filepath, anchors):
    with open(filepath, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["A", "x", "y", "range"])
        writer.writeheader()
        for anchor in anchors:
            writer.writerow(anchor)

@app.route('/')
def home():
    return render_template("home.html")

@app.route('/new_project', methods=["GET", "POST"])
def new_project():
    if request.method == "POST":
        project_id = request.form.get("project_id")
        project_path = os.path.join(BASE_DIR, project_id)

        if not os.path.exists(project_path):
            os.mkdir(project_path)

        csv_path = os.path.join(project_path, f"{project_id}.csv")

        distance_a1 = float(request.form.get("distance_a1"))
        distance_a2 = float(request.form.get("distance_a2"))
        a1 = {"A": "A1", "x": distance_a1, "y": 0.0, "range": distance_a1}
        a2 = {"A": "A2", "x": -distance_a2, "y": 0.0, "range": distance_a2}

        anchors = [a1, a2]

        anchor_index = 3
        while True:
            distance_a1_key = f"distance_a{anchor_index}_a1"
            distance_a2_key = f"distance_a{anchor_index}_a2"
            if distance_a1_key not in request.form or distance_a2_key not in request.form:
                break

            d1 = float(request.form.get(distance_a1_key))
            d2 = float(request.form.get(distance_a2_key))

            x = (d1**2 - d2**2 + (a2["x"] - a1["x"])**2) / (2 * (a2["x"] - a1["x"]))
            y = math.sqrt(max(d1**2 - x**2, 0))
            anchors.append({"A": f"A{anchor_index}", "x": round(x, 4), "y": round(y, 4), "range": round(d1, 4)})

            anchor_index += 1

        save_anchors_to_csv(csv_path, anchors)
        return render_template("success.html", message=f"Project {project_id} created successfully!")

    return render_template("new_project.html")

@app.route('/edit_project', methods=["GET", "POST"])
def edit_project():
    if request.method == "POST":
        project_id = request.form.get("project_id")
        project_path = os.path.join(BASE_DIR, project_id)
        csv_path = os.path.join(project_path, f"{project_id}.csv")

        if not os.path.exists(csv_path):
            return render_template("error.html", message="The selected project does not exist.")

        return redirect(url_for('edit_specific_project', project_id=project_id))

    projects = [d for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d))]
    return render_template("edit_project.html", projects=projects)

@app.route('/edit_project/<project_id>', methods=["GET", "POST"])
def edit_specific_project(project_id):
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
                "range": float(request.form.getlist("range")[i])
            })
        save_anchors_to_csv(csv_path, anchors)
        return render_template("success.html", message=f"Project {project_id} updated successfully!")

    anchors = []
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            anchors.append(row)

    return render_template("edit_specific_project.html", project_id=project_id, anchors=anchors)


@app.route('/update', methods=["GET", "POST"])
def update():
    try:
        projects = []
        for project_name in os.listdir(BASE_DIR):
            project_path = os.path.join(BASE_DIR, project_name)
            csv_path = os.path.join(project_path, f"{project_name}.csv")
            if os.path.exists(csv_path):
                modification_time = os.path.getmtime(csv_path)
                formatted_time = datetime.fromtimestamp(modification_time).strftime('%Y-%m-%d %H:%M:%S')
                projects.append({"name": project_name, "timestamp": formatted_time})

        if request.method == "POST":
            # Handle the dropdown CSV file selection
            project_id = request.form.get("selected_project")
            if project_id:
                project_path = os.path.join(BASE_DIR, project_id)
                csv_path = os.path.join(project_path, f"{project_id}.csv")

                if os.path.exists(csv_path):
                    with open(csv_path, newline='') as csvfile:
                        reader = csv.DictReader(csvfile)
                        anchors = [row for row in reader]

                    # Prepare anchor data in the required format for the ESP32
                    anchor_data = {
                        "anchors": [
                            {
                                "A": anchor["A"],
                                "x": float(anchor["x"]),
                                "y": float(anchor["y"]),
                                "range": float(anchor["range"])
                            }
                            for anchor in anchors
                        ]
                    }

                    # Log the anchor data for debugging
                    print(f"Sending the following data to ESP32: {json.dumps(anchor_data, indent=2)}")

                    # Send the anchor data to ESP32
                    esp32_url = "http://192.168.1.184/save"  # Replace with the ESP32 IP address
                    headers = {'Content-Type': 'application/json'}
                    response = requests.post(esp32_url, json=anchor_data, headers=headers)

                    # Check for response status
                    if response.status_code == 200:
                        print("Data sent successfully")
                        return render_template(
                            "update.html",
                            projects=projects,
                            selected_project={
                                "name": project_id,
                                "anchors": anchors
                            },
                            message="Anchor data updated successfully!"
                        )
                    else:
                        print(f"Failed to update: {response.status_code}, {response.text}")
                        return render_template(
                            "update.html",
                            projects=projects,
                            selected_project={
                                "name": project_id,
                                "anchors": anchors
                            },
                            message="Failed to update anchor data on ESP32."
                        )

        # Initial GET request
        return render_template("update.html", projects=projects, selected_project=None)

    except Exception as e:
        print(f"Error in /update: {e}")
        return render_template("error.html", message="An error occurred during the update process.")


if __name__ == '__main__':
    app.run(debug=True)
