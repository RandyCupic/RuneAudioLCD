import RPi.GPIO as GPIO
import time

# This class will send commands to MPD client from buttons
class buttons():
	# Class constructor
	# Buttons pins is a dictionary with button_name=>pin_number format
	def __init__(self, button_pins, bounce_time):
		# Set bounce time
		self.bounce_time = bounce_time
		
		# Set buttons
		self.buttons = button_pins
	
		# Set GPIO numbering mode
		GPIO.setmode(GPIO.BOARD)
		
		# We don't need warnings from GPIO
		GPIO.setwarnings(False)
		
		# Set button GPIO pins as inputs and enable interrupts
		for button in button_pins:
			if (button_pins[button] != False):
				GPIO.setup(button_pins[button], GPIO.IN, pull_up_down = GPIO.PUD_UP)
				GPIO.add_event_detect(button_pins[button], GPIO.FALLING, callback=self.button_pressed, bouncetime=self.bounce_time)
			
		# Initalize MPD
		self.mpd = False
			
	# Register MPD client to send it commands
	def register(self, mpd):
		self.mpd = mpd
			
	def button_pressed(self, channel):
		# Debouncing
		time.sleep(0.05)
		if (GPIO.input(channel) == 0):
			# Find out which button was pressed
			for button in self.buttons:
				if (channel == self.buttons[button]):					
					# Send command to MPD client
					if (self.mpd != False):
						self.mpd.commands(button.replace('_BUTTON', ''))