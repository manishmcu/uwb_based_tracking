#include <WiFi.h>
#include <ESPAsyncWebServer.h>
#include <ArduinoJson.h>
#include <Preferences.h>

// Replace with your network credentials
const char* ssid = "Digitaiken";
const char* password = "Welcome@123";
String anchorData;
// Set static IP and Gateway
IPAddress local_ip(192, 168, 1, 184);
IPAddress gateway(192, 168, 1, 1);
IPAddress subnet(255, 255, 255, 0);

// Create AsyncWebServer object on port 80
AsyncWebServer server(80);

// Create Preferences object for storing data
Preferences preferences;

void setup() {
  Serial.begin(115200);

  // Initialize preferences storage
  preferences.begin("my_app", false);

  // Configure WiFi
  WiFi.config(local_ip, gateway, subnet);
  WiFi.begin(ssid, password);

  // Wait for WiFi connection
  Serial.println("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  // Retrieve and print stored anchor data at boot
  anchorData = preferences.getString("anchorData", "No data found");
  Serial.println("Stored Anchor Data at Boot:");
  Serial.println(anchorData);

  // Handle POST requests to save anchor data
  server.on("/save", HTTP_POST, [](AsyncWebServerRequest *request) {}, NULL,
    [](AsyncWebServerRequest *request, uint8_t *data, size_t len, size_t index, size_t total) {
      // Allocate buffer for dynamic JSON size
      DynamicJsonDocument doc(2048);

      // Parse incoming JSON
      DeserializationError error = deserializeJson(doc, data, len);
      if (error) {
        // Return error if JSON parsing fails
        request->send(400, "application/json", "{\"status\":\"Invalid JSON format\"}");
        Serial.print("JSON deserialization error: ");
        Serial.println(error.f_str());
        return;
      }

      // Validate the structure of the JSON
      if (!doc.containsKey("anchors") || !doc["anchors"].is<JsonArray>()) {
        request->send(400, "application/json", "{\"status\":\"Invalid JSON structure\"}");
        Serial.println("Invalid JSON structure received");
        return;
      }

      // Save JSON data as a string in preferences
      String jsonPayload;
      serializeJson(doc, jsonPayload);
      preferences.putString("anchorData", jsonPayload);

      // Log the received data
      Serial.println("Received and saved anchor data:");
      Serial.println(jsonPayload);

      // Send success response
      request->send(200, "application/json", "{\"status\":\"Data saved successfully\"}");
    }
  );

  // Serve GET requests to retrieve stored data
  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request) {
    // Retrieve anchor data from preferences
    String anchorData = preferences.getString("anchorData", "No data found");
    request->send(200, "application/json", anchorData);
  });

  // Start the server
  server.begin();
}

void loop() {
  delay(1000);
//  Serial.println(anchorData);
}
