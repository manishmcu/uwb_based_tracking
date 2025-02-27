#include <WiFi.h>
#include <ESPAsyncWebServer.h>
#include <HardwareSerial.h>
#include <math.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Preferences.h>
#include <algorithm> // For sorting

// Wi-Fi credentials
const char* ssid = "Digitaiken";
const char* password = "Welcome@123";

// Static IP Configuration
IPAddress local_IP(192, 168, 1, 34);
IPAddress gateway(192, 168, 1, 1);
IPAddress subnet(255, 255, 255, 0);

// Web server on port 80
AsyncWebServer server(80);

// Anchor data structure
struct Anchor {
  int id;
  float x, y, range;
};

// List of anchors
std::vector<Anchor> anchors;

// Hardware Serial for UWB module
HardwareSerial mySerial(1);
#define RX_PIN 20
#define TX_PIN 21

Preferences preferences;

// Trilateration function
bool trilateration(const std::vector<Anchor>& closestAnchors, float& x, float& y) {
  if (closestAnchors.size() < 3) return false;

  // Use the three closest anchors for calculation
  float x1 = closestAnchors[0].x, y1 = closestAnchors[0].y, d1 = closestAnchors[0].range;
  float x2 = closestAnchors[1].x, y2 = closestAnchors[1].y, d2 = closestAnchors[1].range;
  float x3 = closestAnchors[2].x, y3 = closestAnchors[2].y, d3 = closestAnchors[2].range;

  // Formulate the equations
  float A = 2 * (x2 - x1);
  float B = 2 * (y2 - y1);
  float C = pow(d1, 2) - pow(d2, 2) - pow(x1, 2) + pow(x2, 2) - pow(y1, 2) + pow(y2, 2);

  float D = 2 * (x3 - x2);
  float E = 2 * (y3 - y2);
  float F = pow(d2, 2) - pow(d3, 2) - pow(x2, 2) + pow(x3, 2) - pow(y2, 2) + pow(y3, 2);

  // Solve for x and y
  y = (F - D * C / A) / (E - D * B / A);
  x = (C - B * y) / A;

  return true;
}

// Function to send AT command to UWB module
void sendATCommand(String command) {
  mySerial.println(command);  // Send the command
  delay(1);
}

// Function to fetch anchors from a webhost
void fetchAnchorData() {
  HTTPClient http;
  http.begin("http://example.com/anchors");  // Replace with your server URL
  int httpResponseCode = http.GET();

  if (httpResponseCode == 200) {
    String payload = http.getString();

    // Parse JSON data
    DynamicJsonDocument doc(1024);
    DeserializationError error = deserializeJson(doc, payload);

    if (!error) {
      anchors.clear();  // Clear the existing anchors
      JsonArray anchorArray = doc["anchors"].as<JsonArray>();

      for (JsonObject anchorObj : anchorArray) {
        Anchor anchor;
        anchor.id = anchorObj["A"];
        anchor.x = anchorObj["x"];
        anchor.y = anchorObj["y"];
        anchor.range = 0;  // Initialize range to 0
        anchors.push_back(anchor);
      }

      // Save to NVS for future use
      preferences.putString("anchorData", payload);
    } else {
      Serial.println("Failed to parse JSON data");
    }
  } else {
    Serial.println("Failed to fetch anchor data, loading from NVS");

    // Load from NVS
    String savedData = preferences.getString("anchorData", "");
    if (!savedData.isEmpty()) {
      DynamicJsonDocument doc(1024);
      if (!deserializeJson(doc, savedData)) {
        anchors.clear();
        JsonArray anchorArray = doc["anchors"].as<JsonArray>();

        for (JsonObject anchorObj : anchorArray) {
          Anchor anchor;
          anchor.id = anchorObj["A"];
          anchor.x = anchorObj["x"];
          anchor.y = anchorObj["y"];
          anchor.range = 0;
          anchors.push_back(anchor);
        }
      }
    }
  }

  http.end();
}

// Function to read UWB ranges and update anchors
void readUWBData() {
  if (mySerial.available()) {
    String response = "";

    while (mySerial.available()) {
      char c = mySerial.read();
      response += c;
      delay(1);
    }

    // Example response parsing logic
    for (auto& anchor : anchors) {
      String searchTerm = "distance" + String(anchor.id) + ":";
      if (response.indexOf(searchTerm) != -1) {
        int idx = response.indexOf(searchTerm) + searchTerm.length();
        anchor.range = response.substring(idx, response.indexOf("m", idx)).toFloat();
      }
    }
  }
}

// Function to find the three closest anchors
std::vector<Anchor> getClosestAnchors() {
  std::vector<Anchor> sortedAnchors = anchors;

  // Sort anchors based on range
  std::sort(sortedAnchors.begin(), sortedAnchors.end(), [](const Anchor& a, const Anchor& b) {
    return a.range < b.range;
  });

  // Return the closest three anchors
  if (sortedAnchors.size() > 3) {
    sortedAnchors.resize(3);
  }
  return sortedAnchors;
}

void setup() {
  // Initialize serial and preferences
  Serial.begin(115200);
  mySerial.begin(115200, SERIAL_8N1, RX_PIN, TX_PIN);
  sendATCommand("AT+switchdis=1");
  preferences.begin("UWB", false);

  // Configure Wi-Fi
  if (!WiFi.config(local_IP, gateway, subnet)) {
    Serial.println("Failed to configure static IP");
  }
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWi-Fi Connected!");

  // Fetch anchor data
  fetchAnchorData();

  // Define HTTP routes
  server.on("/", HTTP_GET, [](AsyncWebServerRequest* request) {
    request->send(200, "text/plain", "UWB Positioning System Running");
  });

  server.on("/get_position", HTTP_GET, [](AsyncWebServerRequest* request) {
    float x = 0, y = 0;
    auto closestAnchors = getClosestAnchors();
    if (trilateration(closestAnchors, x, y)) {
      String response = "Tag Position: (" + String(x, 4) + ", " + String(y, 4) + ")\n";
      for (const auto& anchor : closestAnchors) {
        response += "A" + String(anchor.id) + ": (" + String(anchor.x, 4) + ", " + String(anchor.y, 4) + "), Range: " + String(anchor.range, 4) + "m\n";
      }
      request->send(200, "text/plain", response);
    } else {
      request->send(200, "text/plain", "Not enough anchors for trilateration.");
    }
  });

  server.begin();
}

void loop() {
  // Update UWB ranges dynamically
  readUWBData();

  // Debug output
  float x, y;
  auto closestAnchors = getClosestAnchors();
  if (trilateration(closestAnchors, x, y)) {
    Serial.print("Tag Position: (");
    Serial.print(x, 4);
    Serial.print(", ");
    Serial.print(y, 4);
    Serial.println(")");
  } else {
    Serial.println("Not enough anchors for trilateration.");
  }

  delay(500);
}
