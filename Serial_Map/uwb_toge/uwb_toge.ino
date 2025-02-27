#include <HardwareSerial.h>
#include <math.h>

// Constants
float distance_a1_a2 = 6.6;  // Distance between Anchor-1 and Anchor-2 (meters)
float meter2pixel = 100;      // Conversion factor from meters to pixels
float range_offset = 0.9;     // Range offset for adjustment

// Global variables for range (ensure they are floats)
float a1_range = 3.5;  // Distance from Anchor-1 (in meters)
float a2_range = 4.5;  // Distance from Anchor-2 (in meters)

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

  // Print the current range data
  Serial.print("Anchor-1 range: ");
  Serial.print(a1_range);
  Serial.println(" meters");

  Serial.print("Anchor-2 range: ");
  Serial.print(a2_range);
  Serial.println(" meters");

  // Calculate the position of the tag
  float x, y;
  trilateration(a1_range, a2_range, distance_a1_a2, x, y);

  // Print the position of the tag
  Serial.print("Tag position: (");
  Serial.print(x, 2);  // Print the x-coordinate with 2 decimal places
  Serial.print(", ");
  Serial.print(y, 2);  // Print the y-coordinate with 2 decimal places
  Serial.println(")");

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

    // Debug print received data
    Serial.println("Received data:");
    Serial.println(response);

    // Extract distances using string parsing
    if (response.indexOf("distance0:") != -1 && response.indexOf("distance1:") != -1) {
      int idx1 = response.indexOf("distance0:") + 10;
      int idx2 = response.indexOf("distance1:") + 10;

      a1_range = response.substring(idx1, response.indexOf("m", idx1)).toFloat();
      a2_range = response.substring(idx2, response.indexOf("m", idx2)).toFloat();

      // Debug print the extracted distances
      Serial.print("Extracted a1_range: ");
      Serial.println(a1_range);
      Serial.print("Extracted a2_range: ");
      Serial.println(a2_range);
    }
  }
}

// Function to send AT command to UWB module
void sendATCommand(String command) {
  mySerial.println(command);  // Send AT command
  delay(1);  // Delay of 1ms to give the UWB module time to process
}

// Trilateration function to compute tag position
void trilateration(float d1, float d2, float distance_a1_a2, float &x, float &y) {
  // Anchor positions (Anchor-1 at (0,0) and Anchor-2 at (distance_a1_a2, 0))
  float x1 = 0.0, y1 = 0.0;  // Position of Anchor-1
  float x2 = distance_a1_a2, y2 = 0.0;  // Position of Anchor-2
  
  // Trilateration calculations (2D position)
  float A = 2.0 * (x2 - x1);
  float B = 2.0 * (y2 - y1);
  float C = d1 * d1 - d2 * d2 - x1 * x1 + x2 * x2 - y1 * y1 + y2 * y2;

  x = C / A;

  // Ensure no negative square roots
  float y_value = d1 * d1 - x * x;
  if (y_value < 0) {
    y = 0;
  } else {
    y = sqrt(y_value);
  }
}
