# Code Versions Guidelines  

Each `web_app` folder contains:  
- `app.py` – Python Flask web server for controlling the robot or configuring anchors.  
- `templates/` – HTML templates used by `app.py` for the web interface.  
- `web_uwb_toge.ino` – ESP32-C3 firmware for retrieving UWB sensor data over the network.  

### **web_app**  
- `app.py`:  
  - Runs a Flask web server on Windows for robot control and anchor configuration.  
  - Scans the network (`get_ip_addresses()` via `nmap`) to discover robots.  
  - Validates devices (`check_if_robot()`) and assigns URLs for movement and cancellation commands.  
  - Fetches position data from the overlay API (`fetch_position_data()`) for real-time tracking.  
  - Provides web endpoints (`/start_tracking`, `/stop_tracking`, `/call`, `/cancel`) for user interaction at `http://127.0.0.1:5000/`.  
  - Uses `ThreadPoolExecutor` for concurrent IP scanning and `Timer` for scheduling tasks.  

- `web_uwb_toge.ino`:  
  - Implements UWB-based positioning with an ESP32 (static IP for stable connectivity).  
  - Hosts an asynchronous web server (`ESPAsyncWebServer`) to serve `get_position` (trilateration) and `get_ranges` (raw distance data).  
  - Communicates with the UWB module via `HardwareSerial`, computes tag position, and logs data to the serial monitor.  

### **web_app2**  
- `app.py`:  
  - Flask web server for managing anchor data in CSV format under `projects/`.  
  - Uses a Jinja2 filter (`datetimeformat`) for timestamps and trigonometry (`calculate_coordinates()`) for anchor positions.  
  - Provides `/` for project listing, `/new_project` for capturing distances, `/edit_project` for modification, and `/update` to send anchor data to an ESP32 endpoint.  
  - Ensures ESP32 data validation and error handling.  

- `web_uwb_toge.ino`:  
  - ESP32 web server with `ESPAsyncWebServer` for GET/POST requests.  
  - Stores/retrieves anchor data using `Preferences.h` and `ArduinoJson`.  
  - Receives JSON anchor data via POST, saves it persistently, and serves stored data via GET.  

### **web_app3**  
- `app.py`:  
  - Flask web server for project-based ESP32 communication.  
  - Uses `BASE_DIR` for storing project files, `calculate_coordinates()` for anchor positions, and CSV for data storage.  
  - Provides `/` for homepage, `/new_project` for creating projects, `/edit_project` for modifications, `/get_ranges` for ESP32 range data, and `/update` to send anchor data.  
  - Implements `/live_distances` for real-time ESP32 distance tracking.  

- `web_uwb_toge.ino`:  
  - ESP32 firmware enabling Wi-Fi-based positioning.  
  - Hosts `ESPAsyncWebServer` to handle `get_position` (trilateration) and `save` (anchor data storage).  
  - Uses `Preferences.h` for persistent storage and `ArduinoJson` for JSON parsing.  
  - Fetches real-time UWB distance data via UART, processes it, and provides updates through `/get_ranges`.  
