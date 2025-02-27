import pygame
import serial
import time

# Constants
distance_a1_a2 = 6.6  # Distance between Anchor-1 and Anchor-2 (meters)
meter2pixel = 50  # Conversion factor from meters to pixels
screen_width, screen_height = 1200, 800  # Screen size
serial_port = 'COM9'  # Set your COM port
baud_rate = 115200  # Baud rate for serial communication

# Setup Pygame
pygame.init()
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("UWB Position Map")
clock = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)

def draw_anchor(x, y, txt, range):
    """Draw the anchor and its range on the map."""
    pygame.draw.circle(screen, GREEN, (x, y), 20)
    font = pygame.font.SysFont('Arial', 16)
    label = font.render(f"{txt}: {range}M", True, BLACK)
    screen.blit(label, (x + 25, y - 10))

def draw_tag(x, y, txt):
    """Draw the tag position on the map."""
    # Adjust for the conversion factor and screen centering
    pos_x = int(x * meter2pixel) + 250  # Center tag in the screen
    pos_y = screen_height - int(y * meter2pixel) - 150  # Adjust Y position to match the bottom layout
    
    # Ensure tag is within the screen bounds
    if 0 < pos_x < screen_width and 0 < pos_y < screen_height:
        pygame.draw.circle(screen, BLUE, (pos_x, pos_y), 20)
        font = pygame.font.SysFont('Arial', 16)
        label = font.render(f"{txt}: ({x},{y})", True, BLACK)
        screen.blit(label, (pos_x + 25, pos_y - 10))
    else:
        print(f"Tag out of bounds: ({pos_x}, {pos_y})")

def read_serial_data():
    """Read and parse serial data for tag position and anchor ranges."""
    try:
        with serial.Serial(serial_port, baud_rate, timeout=1) as ser:
            while True:
                # Read the serial input line by line
                line = ser.readline().decode('utf-8').strip()
                if line.startswith("Anchor-1 range"):
                    a1_range = float(line.split(":")[1].split()[0])  # Extract Anchor-1 range
                elif line.startswith("Anchor-2 range"):
                    a2_range = float(line.split(":")[1].split()[0])  # Extract Anchor-2 range
                elif line.startswith("Tag position"):
                    tag_position = line.split(":")[1].strip()[1:-1]  # Extract tag position (x, y)
                    tag_x, tag_y = map(float, tag_position.split(","))
                    return a1_range, a2_range, tag_x, tag_y
    except serial.SerialException as e:
        print(f"Error reading from serial port: {e}")
        return None, None, None, None

def main():
    running = True
    while running:
        screen.fill(WHITE)  # Clear screen

        # Handle events (exit on close)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Read serial data
        a1_range, a2_range, tag_x, tag_y = read_serial_data()
        
        if a1_range is not None and a2_range is not None and tag_x is not None and tag_y is not None:
            # Draw anchors - Move anchors to the bottom of the screen
            anchor_y = screen_height - 150  # Adjust Y position of anchors to be closer to the bottom
            draw_anchor(250, anchor_y, "A1782(0,0)", a1_range)
            draw_anchor(250 + int(distance_a1_a2 * meter2pixel), anchor_y, f'A1783({distance_a1_a2},0)', a2_range)  # Correct string formatting

            # Draw the tag position on the map
            draw_tag(tag_x, tag_y, "TAG")

        # Update the display
        pygame.display.update()

        # Cap the frame rate to 10 FPS
        clock.tick(10)

    pygame.quit()

if __name__ == '__main__':
    main()
