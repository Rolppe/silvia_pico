from machine import Pin, I2C
import time
from enhanced_display import Enhanced_Display
import packed_font

# I2C initialization
i2c = I2C(0, scl=Pin(5), sda=Pin(4))

# Enhanced Display initialization (assuming PiicoDev_SSD1306 is installed)
display = Enhanced_Display(address=0x3C, sda=Pin(4), scl=Pin(5))

# Load your font files (replace 'largefont' and 'smallfont' with actual font names without .pf)
display.load_font('largefont')  # For large temperature text
display.load_font('smallfont')  # For menu and small text

# Buttons
button_up = Pin(6, Pin.IN, Pin.PULL_UP)
button_down = Pin(7, Pin.IN, Pin.PULL_UP)

# Menu items
menu_items = ["Option 1", "Option 2", "Option 3", "Option 4"]
selected = 0
in_menu = False

def draw_default():
    display.fill(0)
    # Select large font for temperature
    display.select_font('largefont')
    # Large temperature text (dummy), adjust alignment if needed
    display.text("100 °C", 10, 10, horiz_align=0, vert_align=0)
    # Select small font or built-in for menu symbol
    display.select_font('smallfont')  # Or None for built-in
    # Small menu symbol in top-right (e.g., three dots)
    display.text("...", 110, 0)
    display.show()

def draw_menu():
    display.fill(0)
    # Use small font for menu
    display.select_font('smallfont')  # Or None for built-in
    for i, item in enumerate(menu_items):
        if i == selected:
            display.text(">" + item, 0, i * 10)
        else:
            display.text(" " + item, 0, i * 10)
    display.show()

draw_default()

while True:
    if not button_up.value():  # Up button pressed
        if not in_menu:
            in_menu = True
            draw_menu()
        else:
            # Select item in menu
            display.fill(0)
            display.select_font('smallfont')
            display.text("Selected: " + menu_items[selected], 0, 0)
            display.show()
            time.sleep(1)
            in_menu = False
            draw_default()
        time.sleep(0.2)
    if not button_down.value() and in_menu:  # Down button pressed in menu
        selected = (selected + 1) % len(menu_items)
        draw_menu()
        time.sleep(0.2)
    time.sleep(0.1)