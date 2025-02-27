import time
import turtle
import cmath
import serial
import re  # For regular expression-based filtering

# Initialize serial port
ser = serial.Serial('COM9', 115200)  # Change COM9 if necessary
time.sleep(2)  # Wait for the serial connection to establish

# Constants
distance_a1_a2 = 6.6  # Distance between Anchor-1 and Anchor-2 (meters)
meter2pixel = 100  # Conversion factor from meters to pixels
range_offset = 0.9  # Range offset for adjustment

# Global variables for range (ensuring they are floats)
a1_range = 3.5  # Distance from Anchor-1 (in meters)
a2_range = 4.5  # Distance from Anchor-2 (in meters)

# Screen and Turtle setup
def screen_init(width=1200, height=800, t=turtle):
    t.setup(width, height)
    t.tracer(1)  # Set to 1 for immediate updates
    t.hideturtle()
    t.speed(0)

def turtle_init(t=turtle):
    t.hideturtle()
    t.speed(0)

def draw_line(x0, y0, x1, y1, color="black", t=turtle):
    t.pencolor(color)
    t.up()
    t.goto(x0, y0)
    t.down()
    t.goto(x1, y1)
    t.up()

def write_txt(x, y, txt, color="black", t=turtle, f=('Arial', 12, 'normal')):
    t.pencolor(color)
    t.up()
    t.goto(x, y)
    t.down()
    t.write(txt, move=False, align='left', font=f)
    t.up()

def fill_cycle(x, y, r, color="black", t=turtle):
    t.up()
    t.goto(x, y)
    t.down()
    t.dot(r, color)
    t.up()

def draw_ui(t):
    write_txt(-300, 250, "UWB Position", "black", t, f=('Arial', 32, 'normal'))
    fill_rect(-400, 200, 800, 40, "black", t)
    write_txt(-50, 205, "WALL", "yellow", t, f=('Arial', 24, 'normal'))

def draw_uwb_anchor(x, y, txt, range, t):
    r = 20
    fill_cycle(x, y, r, "green", t)
    write_txt(x + r, y, txt + ": " + str(range) + "M", "black", t, f=('Arial', 16, 'normal'))

def draw_uwb_tag(x, y, txt, t):
    pos_x = -250 + int(x * meter2pixel)
    pos_y = 150 - int(y * meter2pixel)
    r = 20
    fill_cycle(pos_x, pos_y, r, "blue", t)
    write_txt(pos_x, pos_y, txt + ": (" + str(x) + "," + str(y) + ")", "black", t, f=('Arial', 16, 'normal'))

def fill_rect(x, y, w, h, color="black", t=turtle):
    t.begin_fill()
    draw_rect(x, y, w, h, color, t)
    t.end_fill()

def draw_rect(x, y, w, h, color="black", t=turtle):
    t.pencolor(color)
    t.up()
    t.goto(x, y)
    t.down()
    t.goto(x + w, y)
    t.goto(x + w, y + h)
    t.goto(x, y + h)
    t.goto(x, y)
    t.up()

def read_data():
    global a1_range, a2_range  # Declare a1_range and a2_range as global
    
    # Read all lines from the serial input
    line = ser.readline().decode('UTF-8').strip()  # Read and clean up the serial line

    # Print the raw data for debugging purposes
    print(f"Raw data: {line}")
    
    # Only process valid distance data lines
    if "distance" in line:
        distances = []

        # Use regex to extract distance values (distanceX:value format)
        distance_pattern = re.compile(r'distance(\d+):(\d+\.?\d*)m')

        # Search for all matches
        matches = distance_pattern.findall(line)
        
        if matches:
            # Process each match and assign the corresponding distance to a1_range or a2_range
            for match in matches:
                x_value = int(match[0])  # DistanceX identifier
                distance_value = float(match[1])  # Distance value (ensure it's a float)
                
                if x_value == 0:
                    a1_range = distance_value
                elif x_value == 1:
                    a2_range = distance_value
            
            # Debug print to check if distances are being extracted and assigned
            print(f"a1_range: {a1_range}, a2_range: {a2_range}")
        
        return a1_range, a2_range
    else:
        return None, None  # Return None if the line doesn't contain valid data

# Add the missing 'clean' function
def clean(t):
    t.clear()  # This clears the turtle's drawing on the screen

def trilateration(d1, d2, distance_a1_a2):
    """Calculate the position of the tag using trilateration."""
    # Ensure all distances are floats
    d1, d2, distance_a1_a2 = float(d1), float(d2), float(distance_a1_a2)
    
    # Assuming Anchor-1 is at (0, 0) and Anchor-2 is at (distance_a1_a2, 0)
    x1, y1 = 0.0, 0.0  # Position of Anchor-1
    x2, y2 = distance_a1_a2, 0.0  # Position of Anchor-2
    
    # Using the trilateration formula
    A = 2.0 * (x2 - x1)
    B = 2.0 * (y2 - y1)
    C = d1 ** 2 - d2 ** 2 - x1 ** 2 + x2 ** 2 - y1 ** 2 + y2 ** 2
    
    x = C / A  # Calculate x
    
    # Ensure the square root value is non-negative
    y_value = d1 ** 2 - x ** 2  # The value for the y calculation
    
    if y_value < 0:
        print(f"Warning: Negative value under square root: {y_value}. Setting y to 0.")
        y = 0  # Or handle it in some other way
    else:
        y = y_value ** 0.5  # Calculate y using square root

    return x, y


def main():
    # Setup Turtle window
    t_ui = turtle.Turtle()
    t_a1 = turtle.Turtle()
    t_a2 = turtle.Turtle()
    t_a3 = turtle.Turtle()
    turtle_init(t_ui)
    turtle_init(t_a1)
    turtle_init(t_a2)
    turtle_init(t_a3)

    # Draw UI
    draw_ui(t_ui)

    while True:
        # Update a1_range and a2_range from the serial data
        read_data()

        print(f"Anchor-1 range: {a1_range} meters")
        print(f"Anchor-2 range: {a2_range} meters")

        # Clear and draw anchors
        clean(t_a1)
        draw_uwb_anchor(-250, 150, "A1782(0,0)", a1_range, t_a1)
        
        clean(t_a2)
        draw_uwb_anchor(-250 + meter2pixel * distance_a1_a2, 150, "A1783(" + str(distance_a1_a2) + ")", a2_range, t_a2)

        # Calculate the position of the tag
        x, y = trilateration(a1_range, a2_range, distance_a1_a2)
        print(f"Tag position: ({x}, {y})")

        # Draw the tag position on the screen
        clean(t_a3)
        draw_uwb_tag(x, y, "TAG", t_a3)

        # Update the screen with the new drawings
        turtle.update()

        # Sleep for a short period before updating again
        time.sleep(0.1)

    turtle.mainloop()

if __name__ == '__main__':
    screen_init()  # Initialize the turtle screen
    main()
