import time
import turtle
import cmath
import serial
import re  # For regular expression-based filtering

# Initialize serial port
ser = serial.Serial('COM9', 115200)  # Change COM9 if necessary
time.sleep(2)  # Wait for the serial connection to establish

# Constants
distance_a1_a2 = 3.0  # Distance between Anchor-1 and Anchor-2 (meters)
meter2pixel = 100  # Conversion factor from meters to pixels
range_offset = 0.9  # Range offset for adjustment

# Screen and Turtle setup
def screen_init(width=1200, height=800, t=turtle):
    t.setup(width, height)
    t.tracer(False)
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

def read_data():
    # Read all lines from the serial input
    line = ser.readline().decode('UTF-8').strip()  # Read and clean up the serial line

    # Print the raw data for debugging purposes
    print(f"Raw data: {line}")
    
    # Only process valid distance data lines
    if "distance" in line:
        distances = []

        # Use regex to extract distance values (distanceX:value format)
        distance_pattern = re.compile(r'distance\d+:(\d+\.?\d*)m')

        # Search for all matches
        matches = distance_pattern.findall(line)
        
        if matches:
            # Convert matches to float and store them as distances
            distances = [float(dist) for dist in matches]
        
        # Debug print to check if distances are being extracted
        print(f"Distances extracted: {distances}")
        
        return distances
    else:
        return []  # Return an empty list if the line doesn't contain valid data

def tag_pos(a, b, c):
    # Use triangulation formula to calculate tag position
    cos_a = (b * b + c * c - a * a) / (2 * b * c)
    x = b * cos_a
    y = b * cmath.sqrt(1 - cos_a * cos_a)
    return round(x.real, 1), round(y.real, 1)

def uwb_range_offset(uwb_range):
    # Apply any offsets or adjustments if needed
    return uwb_range

def main():
    t_ui = turtle.Turtle()
    t_a1 = turtle.Turtle()
    t_a2 = turtle.Turtle()
    t_a3 = turtle.Turtle()
    turtle_init(t_ui)
    turtle_init(t_a1)
    turtle_init(t_a2)
    turtle_init(t_a3)

    draw_ui(t_ui)

    while True:
        # Read and process the data
        distA = read_data()

        if len(distA) == 2:  # We expect distances from exactly two anchors
            a1_range = distA[0]  # Distance from Anchor-1
            a2_range = distA[1]  # Distance from Anchor-2

            # Debug prints to verify the anchor ranges
            print(f"Anchor-1 range: {a1_range} meters")
            print(f"Anchor-2 range: {a2_range} meters")

            clean(t_a1)
            draw_uwb_anchor(-250, 150, "A1782(0,0)", a1_range, t_a1)
            
            clean(t_a2)
            draw_uwb_anchor(-250 + meter2pixel * distance_a1_a2, 150, "A1783(" + str(distance_a1_a2) + ")", a2_range, t_a2)

            # Calculate the position of the tag
            x, y = tag_pos(a2_range, a1_range, distance_a1_a2)
            print(f"Tag position: ({x}, {y})")

            # Draw the tag position on the screen
            clean(t_a3)
            draw_uwb_tag(x, y, "TAG", t_a3)

        # Sleep for a short period before reading again
        time.sleep(0.1)

    turtle.mainloop()

if __name__ == '__main__':
    main()



