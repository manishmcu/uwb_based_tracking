    
import time
import turtle
import math

# Constants
distance_a1_a2 = 4.5  # Distance between Anchor-1 and Anchor-2 (meters)
meter2pixel = 100  # Conversion factor from meters to pixels

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

# Add the missing 'clean' function
def clean(t):
    t.clear()  # This clears the turtle's drawing on the screen

def trilateration(d1, d2, distance_a1_a2):
    """Calculate the position of the tag using trilateration."""
    # Assuming Anchor-1 is at (0, 0) and Anchor-2 is at (distance_a1_a2, 0)
    x1, y1 = 0, 0  # Position of Anchor-1
    x2, y2 = distance_a1_a2, 0  # Position of Anchor-2
    
    # Using the trilateration formula
    A = 2 * (x2 - x1)
    B = 2 * (y2 - y1)
    C = d1 ** 2 - d2 ** 2 - x1 ** 2 + x2 ** 2 - y1 ** 2 + y2 ** 2
    
    x = C / A
    y = (d1 ** 2 - x ** 2) ** 0.5

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
        # Set dummy distances (these will simulate the distances read from serial)
        a1_range = 2.5  # Distance from Anchor-1 (in meters)
        a2_range = 3.5  # Distance from Anchor-2 (in meters)

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