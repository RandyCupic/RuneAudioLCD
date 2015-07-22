import display

display = display.display(0x27, 4, 20);

display.display_data[0] = "test 1"
display.display_data[1] = "test 2"
display.display_data[2] = "test 3"
display.display_data[3] = "test 4"

display.update_display()
display.backlight(True)