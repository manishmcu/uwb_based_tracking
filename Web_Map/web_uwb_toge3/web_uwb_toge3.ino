#include <WiFi.h>
#include <ESPAsyncWebServer.h>
#include <HardwareSerial.h>
#include <math.h>

// Wi-Fi credentials
const char* ssid = "Digitaiken";      // Replace with your Wi-Fi SSID
const char* password = "Welcome@123"; // Replace with your Wi-Fi password

// Static IP Configuration
IPAddress local_IP(192, 168, 1, 34);  // Static IP address (change as needed)
IPAddress gateway(192, 168, 1, 1);     // Gateway (usually your router's IP)
IPAddress subnet(255, 255, 255, 0);    // Subnet mask

// Web server on port 80
AsyncWebServer server(80);

// Constants
float meter2pixel = 100.0;  // Conversion factor from meters to pixels (optional for visualization)

// Global variables for ranges (ensure floats for precision)
float a1_range = 4.7;  // Distance from Anchor-1 (in meters)
float a2_range = -3.7;  // Distance from Anchor-2 (in meters)
float a1_height_off = 0., a2_height_off = 0.21;  // Adjust for any range offset due to hardware limitations

// Predefined anchor coordinates (example)
float a1_x = 4.52, a1_y = 0.0;  // Anchor-1 coordinates
float a2_x = -3.50, a2_y = 0.0; // Anchor-2 coordinates

// Hardware Serial communication with UWB module
HardwareSerial mySerial(1);  // Use UART1 for communication
#define RX_PIN 16  // RX pin connected to UWB module
#define TX_PIN 17  // TX pin connected to UWB module

void setup() {
  // Initialize serial monitor for debugging
  Serial.begin(115200);  // Debug serial
  while (!Serial);  // Wait for serial to be ready

  // Initialize UART communication with UWB module
  mySerial.begin(115200, SERIAL_8N1, RX_PIN, TX_PIN);
  sendATCommand("AT+switchdis=1");
  
  // Configure static IP
  if (!WiFi.config(local_IP, gateway, subnet)) {
    Serial.println("Failed to configure static IP");
  }

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWi-Fi Connected!");
  Serial.print("Static IP Address: ");
  Serial.println(WiFi.localIP());

  // Define HTTP routes
  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request) {
    request->send(200, "text/plain", "UWB Positioning System Running");
  });

  // Endpoint to get the tag position
  server.on("/get_position", HTTP_GET, [](AsyncWebServerRequest *request) {
    float x, y;
    float distance_a1_a2 = calculateDistance(a1_x, a1_y, a2_x, a2_y);
    trilateration(a1_x, a1_y, a1_range, a2_x, a2_y, a2_range, distance_a1_a2, x, y);

    String response = "Tag Position: (" + String(x, 4) + ", " + String(y, 4) + ")\n";
    response += "A1 Range: " + String(a1_range, 4) + "m\n";
    response += "A2 Range: " + String(a2_range, 4) + "m\n";
    response += "Anchor Distance: " + String(distance_a1_a2, 4) + "m";
    request->send(200, "text/plain", response);
  });

  // Endpoint to get raw range data
  server.on("/get_ranges", HTTP_GET, [](AsyncWebServerRequest *request) {
    String response = "A1 Range: " + String(a1_range, 4) + "m\n";
    response += "A2 Range: " + String(a2_range, 4) + "m";
    request->send(200, "text/plain", response);
  });

  // Start the server
  server.begin();
  Serial.println("HTTP Server started!");
}

void loop() {
  // Read data from UWB module
  readData();

  // Print tag position to the serial monitor (for debugging)
  float x, y;
  float distance_a1_a2 = calculateDistance(a1_x, a1_y, a2_x, a2_y);
  trilateration(a1_x, a1_y, a1_range, a2_x, a2_y, a2_range, distance_a1_a2, x, y);

  Serial.print("Tag Coordinate: (");
  Serial.print(x, 4);
  Serial.print(", ");
  Serial.print(y, 4);
  Serial.print(") | A1: ");
  Serial.print(a1_range, 4);
  Serial.print("m | A2: ");
  Serial.print(a2_range, 4);
  Serial.print("m | Dist_A1_A2: ");
  Serial.print(distance_a1_a2, 4);
  Serial.println("m");

  delay(500);
}

// Function to read distance data from UWB module
void readData() {
  if (mySerial.available()) {
    String response = "";

    // Read all available data until newline
    while (mySerial.available()) {
      char c = mySerial.read();
      response += c;
      delay(1);
    }

    // Parse distances from the response
    if (response.indexOf("distance0:") != -1 && response.indexOf("distance1:") != -1) {
      int idx1 = response.indexOf("distance0:") + 10;
      int idx2 = response.indexOf("distance1:") + 10;

      a1_range = response.substring(idx1, response.indexOf("m", idx1)).toFloat();
      a2_range = response.substring(idx2, response.indexOf("m", idx2)).toFloat();
      a1_range += a1_height_off;
      a2_range += a2_height_off;
    }
  }
}

// Function to send AT command to UWB module
void sendATCommand(String command) {
  mySerial.println(command);  // Send the command
  delay(1);
}

// Function to calculate Euclidean distance between two points
float calculateDistance(float x1, float y1, float x2, float y2) {
  return sqrt(pow(x2 - x1, 2) + pow(y2 - y1, 2));
}

// Trilateration function to compute tag position
void trilateration(float x1, float y1, float d1, float x2, float y2, float d2, float distance_a1_a2, float &x, float &y) {
  float A = 2.0 * (x2 - x1);
  float B = 2.0 * (y2 - y1);
  float C = pow(d1, 2) - pow(d2, 2) - pow(x1, 2) + pow(x2, 2) - pow(y1, 2) + pow(y2, 2);

  x = C / A;

  float y_value = pow(d1, 2) - pow(x - x1, 2);
  y = y_value >= 0 ? sqrt(y_value) : 0;
}
