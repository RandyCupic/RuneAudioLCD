import display, time

display = display.display(0x27, 4, 20);

display.display_data[0] = "test 1"
display.display_data[1] = "test 2"
display.display_data[2] = "test 3"
display.display_data[3] = "test 4"

display.update_display()
display.backlight(True)

while True:
	for i in range(3):
		pom = True
		for j in range(2):
			time.sleep(1)
			display.show_play_mode(i, pom)
			pom = False