import pygame
import requests
import time

# Constants
distance_a1_a2 = 6.6  # Distance between Anchor-1 and Anchor-2 (meters)
meter2pixel = 50  # Conversion factor from meters to pixels
screen_width, screen_height = 1200, 800  # Screen size
esp32_server_position = "http://192.168.1.34/get_position"  # Replace with your ESP32 IP
esp32_server_ranges = "http://192.168.1.34/get_ranges"  # Replace with your ESP32 IP

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
    pos_x = int(x * meter2pixel) + 250
    pos_y = screen_height - int(y * meter2pixel) - 150
    if 0 < pos_x < screen_width and 0 < pos_y < screen_height:
        pygame.draw.circle(screen, BLUE, (pos_x, pos_y), 20)
        font = pygame.font.SysFont('Arial', 16)
        label = font.render(f"{txt}: ({x:.2f},{y:.2f})", True, BLACK)
        screen.blit(label, (pos_x + 25, pos_y - 10))
    else:
        print(f"Tag out of bounds: ({pos_x}, {pos_y})")

def fetch_position_data():
    """Fetch the position data from the ESP32 server."""
    try:
        response = requests.get(esp32_server_position, timeout=2)
        if response.status_code == 200:
            data = response.text
            print(f"Received Position Data: {data}")
            
            # Parse the position data (tag coordinates and ranges)
            if "Tag Position:" in data:
                parts = data.split("\n")
                position_data = parts[0].split(":")[1].strip()  # Extract (x, y) part
                tag_x, tag_y = map(float, position_data[1:-1].split(","))
                
                a1_range = float(parts[1].split(":")[1].strip().replace('m', ''))
                a2_range = float(parts[2].split(":")[1].strip().replace('m', ''))
                
                return a1_range, a2_range, tag_x, tag_y
            else:
                print("Invalid position data format.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
    return None, None, None, None

def fetch_range_data():
    """Fetch the raw range data from the ESP32 server."""
    try:
        response = requests.get(esp32_server_ranges, timeout=2)
        if response.status_code == 200:
            data = response.text
            print(f"Received Range Data: {data}")
            
            # Example response: "A1 Range: 3.5m | A2 Range: 4.5m"
            if "A1 Range:" in data and "A2 Range:" in data:
                parts = data.split("\n")
                a1_range = float(parts[0].split(":")[1].strip().replace('m', ''))
                a2_range = float(parts[1].split(":")[1].strip().replace('m', ''))
                
                return a1_range, a2_range
            else:
                print("Invalid range data format.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
    return None, None

def main():
    running = True
    while running:
        screen.fill(WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Fetch position data (tag coordinates and anchor ranges)
        a1_range, a2_range, tag_x, tag_y = fetch_position_data()
        
        if a1_range is not None and a2_range is not None and tag_x is not None and tag_y is not None:
            print(f"Tag Position: ({tag_x}, {tag_y})")
            print(f"A1 Range: {a1_range}m | A2 Range: {a2_range}m")

            # Draw the anchors and tag
            anchor_y = screen_height - 150
            draw_anchor(250, anchor_y, "A1(0,0)", a1_range)
            draw_anchor(250 + int(distance_a1_a2 * meter2pixel), anchor_y, "A2(6.6,0)", a2_range)
            draw_tag(tag_x, tag_y, "TAG")

        # Optionally, fetch raw range data
        a1_range, a2_range = fetch_range_data()
        if a1_range is not None and a2_range is not None:
            print(f"Raw Range Data - A1 Range: {a1_range}m | A2 Range: {a2_range}m")

        pygame.display.update()
        clock.tick(10)

    pygame.quit()

if __name__ == "__main__":
    main()
