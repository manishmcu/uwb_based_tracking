#include <HardwareSerial.h>
#include <math.h>

// Constants
float meter2pixel = 100;  // Conversion factor from meters to pixels
float range_offset = 0.9; // Range offset for adjustment

// Global variables for range (ensure they are floats)
float a1_range = 3.5;  // Distance from Anchor-1 (in meters)
float a2_range = 4.5;  // Distance from Anchor-2 (in meters)

// Predefined anchor coordinates
float a1_x = 0.0, a1_y = 0.0;
float a2_x = 6.0, a2_y = 0.0;

// Hardware Serial Communication with UWB Module
HardwareSerial mySerial(1);  // Use UART1 (you can also use UART0 or UART2)
#define RX_PIN 16  // RX Pin connected to UWB module
#define TX_PIN 17  // TX Pin connected to UWB module

void setup() {
  // Start the serial monitor to communicate with the PC
  Serial.begin(115200);  // Serial monitor for debugging
  while (!Serial);  // Wait for serial to be ready

  // Start the hardware serial connection with UWB module
  mySerial.begin(115200, SERIAL_8N1, RX_PIN, TX_PIN);  // Baud rate 115200, 8 data bits, no parity, 1 stop bit

  // Send the AT command to the UWB module
  sendATCommand("AT+switchdis=1");

  // Initial debug message
  Serial.println("UWB Position Visualization");
  Serial.println("----------------------------");

  delay(2000);  // Wait for the serial connection to establish
}

void loop() {
  // Read data from UWB module
  readData();

  // Calculate the distance between the two anchors (Euclidean distance)
  float distance_a1_a2 = calculateDistance(a1_x, a1_y, a2_x, a2_y);

  // Calculate the position of the tag
  float x, y;
  trilateration(a1_x, a1_y, a1_range, a2_x, a2_y, a2_range, distance_a1_a2, x, y);

  // Print the output in the required format
  Serial.print("Tag Coordinate: (");
  Serial.print(x, 2);  // Print x-coordinate with 2 decimal places
  Serial.print(", ");
  Serial.print(y, 2);  // Print y-coordinate with 2 decimal places
  Serial.print(") ");
  Serial.print("A1: ");
  Serial.print(a1_range, 2);  // Anchor-1 range
  Serial.print("m A2: ");
  Serial.print(a2_range, 2);  // Anchor-2 range
  Serial.print("m Dist_A1_A2: ");
  Serial.print(distance_a1_a2, 2);  // Distance between anchors
  Serial.println("m");

  // Wait for a short period before updating again
  delay(100);
}

// Function to read data from UWB module
void readData() {
  if (mySerial.available()) {
    String response = "";
    // Read all the available data until newline
    while (mySerial.available()) {
      char c = mySerial.read();
      response += c;
      delay(1);  // Delay of 1ms between reads (to slow down the serial read)
    }

    // Extract distances using string parsing
    if (response.indexOf("distance0:") != -1 && response.indexOf("distance1:") != -1) {
      int idx1 = response.indexOf("distance0:") + 10;
      int idx2 = response.indexOf("distance1:") + 10;

      a1_range = response.substring(idx1, response.indexOf("m", idx1)).toFloat();
      a2_range = response.substring(idx2, response.indexOf("m", idx2)).toFloat();
    }
  }
}

// Function to send AT command to UWB module
void sendATCommand(String command) {
  mySerial.println(command);  // Send AT command
  delay(1);  // Delay of 1ms to give the UWB module time to process
}

// Function to calculate the Euclidean distance between two points
float calculateDistance(float x1, float y1, float x2, float y2) {
  return sqrt(pow(x2 - x1, 2) + pow(y2 - y1, 2));
}

// Trilateration function to compute tag position
void trilateration(float x1, float y1, float d1, float x2, float y2, float d2, float distance_a1_a2, float &x, float &y) {
  // Use the coordinates and distances from the anchors to find the tag's position
  float A = 2.0 * (x2 - x1);
  float B = 2.0 * (y2 - y1);
  float C = pow(d1, 2) - pow(d2, 2) - pow(x1, 2) + pow(x2, 2) - pow(y1, 2) + pow(y2, 2);

  x = C / A;

  // Ensure no negative square roots
  float y_value = pow(d1, 2) - pow(x, 2);
  if (y_value < 0) {
    y = 0;
  } else {
    y = sqrt(y_value);
  }
}
