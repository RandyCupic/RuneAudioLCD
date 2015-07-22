import i2c_driver as LCD # import I2C driver for LCD display
import time, math

class display:
	# Class constructor, receives I2C address of display (usually it's 0x27, check with i2cdetect)
	# Also, number of rows and columns (for example, 2x16 or 4x20 LCD)
	def __init__(self, address, rows, columns):
		self.rows = rows
		self.columns = columns
		
		# Default update time (period)
		self.period = 0.01 # s
		
		# Initialize LCD
		self.lcd = LCD.lcd(address)
		self.lcd.setWidth(self.columns)
		
		# Create array for storing data for display
		# Each element represents one row, and it contains string
		self.display_data = []
		
		# Fill all rows with empty spaces
		for i in range(0, self.rows):
			self.display_data.append('')
			for j in range(self.columns):
				self.display_data[i] = self.display_data[i] + ' '
				
		# Prepare global data for scrolling
		self.scroll = []
		for i in range(self.columns):
			temp = {'data' : '', 'position' : 0, 'direction' : 0}
			self.scroll.append(temp.copy())
		
		# Select first screen
		self.screen = 0
		
		# Temporary screen (volume, repeat, shuffle...) is off
		self.temporary_screen = False
		
	# We need to register MPD client to be able to retrieve data from it
	def register_mpd(self, mpd):
		self.mpd = mpd
		
	# Function for updating LCD display
	def update_display(self):
		tmp = '';
		# Iterate through all lines
		for i in range(self.rows):
			tmp = tmp + self.display_data[i];
			if (i != (self.rows - 1)):
				tmp = tmp + '\n';

		self.lcd.message(tmp);
	
	# Toggle LCD backlight on/off
	def backlight(self, state):
		if (state):
			self.lcd.backlight(1);
		else:
			self.lcd.backlight(0);
			
	# Function for scrolling text, receives row id and text
	# Every time it's called, it will scroll one character
	# If it reaches the end, it will change direction
	# If the text changes, it will start from scratch
	# It returns the text ready for display; it checks if there's a need to scroll or not
	# It uses global variables for current position, direction and data to scroll
	def scroll_row(self, row, text):
		# Maybe there's no need to scroll
		if (len(text) == self.columns):
			return text
			
		# If text is shorter than LCD width, fill the rest with spaces
		elif (len(text) < self.columns):
			temp = text
			for i in range(self.columns - len(text)):
				temp = temp + ' '
				
			return temp
		
		# Check if text has changed
		if(self.scroll[row]['data'] != text): # scroll[row] is a dictionary with scrolling data for 'row'
			self.scroll[row]['data'] = text # It contains text to scroll (data), position and direction
			self.scroll[row]['position'] = 0 # Start from the beginning
			self.scroll[row]['direction'] = 0 # Reset direction to forwards
		
		# Take the part of the text to currently show on the screen
		temp = self.scroll[row]['data'][scroll[row]['position']:scroll[row]['position']+self.columns]
		
		# If direction is FORWARDS
		if (self.scroll[row]['direction'] == 0):
			# If we've reached the end, let us go backwards (change direction)
			if (scroll[row]['position'] == (len(self.scroll[row]['data']) - self.columns)):
				self.scroll[row]['direction'] = 1 # Set direction to backwards
			else:
				scroll[row]['position'] = scroll[row]['position'] + 1 # Move to next position
				
		# If direction is BACKWARDS
		if (self.scroll[row]['direction'] == 1):
			# If we've reached the beginning, let us go forwards (change direction)
			if (scroll[row]['position'] == 0):
				self.scroll[row]['direction'] = 0 # Set direction to forwards
			else:
				scroll[row]['position'] = scroll[row]['position'] - 1 # Move to next position
				
		return temp
		
	# Function for showing volume screen
	def show_volume(self, volume):
		self.temporary_screen = True # We have to notify the thread to stop it from replacing the screen
		
		# Speaker icon custom characters
		speaker_icon = [ 
				[ 0b00000, 0b00000, 0b00000, 0b00000, 0b11111, 0b10001, 0b10001, 0b10001 ],
				[ 0b00001, 0b00011, 0b00101, 0b01001, 0b10001, 0b00001, 0b00001, 0b00001 ],
				[ 0b10001, 0b10001, 0b10001, 0b11111, 0b00000, 0b00000, 0b00000, 0b00000 ],
				[ 0b00001, 0b00001, 0b00001, 0b10001, 0b01001, 0b00101, 0b00011, 0b00001 ]
		]
		
		# Load custom characters
		self.lcd.lcd_load_custom_chars(speaker_icon)
		
		# Show first part of icon + "volume"
		self.display_data[1] = chr(0) + chr(1) + ' Volume'
		
		# Show second part of icon
		self.display_data[2] = chr(2) + chr(3) + ' '
		
		# If volume is 0 or 100 ...
		if (volume == 0 or volume == 100):
			# Fill spaces between; columns - 3 (2 for icon + space) - 12 (length of 'VolumeMIN' or 'VolumeMAX')
			for i in range(self.columns - 12):
				self.display_data[1] += ' '
		
		# If volume is 0, show minimum and no blocks in third line
		if (volume == 0):
			self.display_data[1] += 'MIN'
			for i in range(self.columns - 3): # -3 for icon (2) and space
				self.display_data[2] += ' '
		
		# If volume is 100, show maximum and all blocks in third line	
		elif (volume == 100):
			self.display_data[1] += 'MAX'
			for i in range(self.columns - 3):
				self.display_data[2] += chr(255)
		
		# Else, show value in % and the corresponding number of blocks
		else:
			# Fill spaces between; columns - 3 (icon + space) - 10 (length of 'VolumeXX %)
			for i in range(self.columns - 13):
				self.display_data[1] += ' '
		
			# Check if there is only one digit and append another space
			if (volume < 10):
				self.display_data[1] += ' '
			
			# Append volume value
			self.display_data[1] += `volume` + ' %'
			
			# Calculate number of blocks to show
			temp = (volume / int(math.ceil((100.0 / (self.columns - 3))))) + 1
			
			# Append the blocks
			for i in range (0, temp):
				self.display_data[2] += chr(255)
			
		# We will leave first line empty for now
		self.display_data[0] = ''
		for i in range(self.columns):
			self.display_data[0] += ' '
		
		# We will leave forth line empty for now
		self.display_data[3] = ''
		for i in range(self.columns):
			self.display_data[3] += ' '
			
		# At the end, update the display
		self.update_display()
		
	# Function for showing shuffle (0), repeat all (1) or repeat single (2) screen
	def show_play_mode(self, type, state):
		self.temporary_screen = True # We have to notify the thread to stop it from replacing the screen
		
		# Shuffle icon custom characters
		shuffle_icon = [ 
				[ 0b00000, 0b00000, 0b00000, 0b11100, 0b00010, 0b00010, 0b00010, 0b00001 ], 
				[ 0b00000, 0b00000, 0b00010, 0b00111, 0b01010, 0b01000, 0b01000, 0b10000 ], 
				[ 0b00001, 0b00010, 0b00010, 0b00010, 0b11100, 0b00000, 0b00000, 0b00000 ], 
				[ 0b10000, 0b01000, 0b01000, 0b01010, 0b00111, 0b00010, 0b00000, 0b00000 ]
		]
		
		repeat_all_icon = [ 
				[ 0b00000, 0b00000, 0b00000, 0b00011, 0b00100, 0b01000, 0b10000, 0b10000 ], 
				[ 0b00000, 0b00000, 0b00000, 0b11000, 0b00101, 0b00011, 0b00111, 0b00000 ], 
				[ 0b10000, 0b10000, 0b01000, 0b00100, 0b00011, 0b00000, 0b00000, 0b00000 ],
				[ 0b00000, 0b00000, 0b00010, 0b00100, 0b11000, 0b00000, 0b00000, 0b00000 ]
		]
		
		repeat_single_icon = [ 
				[ 0b00000, 0b00000, 0b00000, 0b00011, 0b00100, 0b01000, 0b00000, 0b00000 ], 
				[ 0b00000, 0b00000, 0b00000, 0b11000, 0b00101, 0b00011, 0b00111, 0b00000 ], 
				[ 0b00000, 0b11100, 0b11000, 0b10100, 0b00011, 0b00000, 0b00000, 0b00000 ],
				[ 0b00000, 0b00000, 0b00010, 0b00100, 0b11000, 0b00000, 0b00000, 0b00000 ]
		]
		
		# Choose icon and text, according to type
		if (type == 0):
			icon = shuffle_icon
			text = "Shuffle Mode"
		elif (type == 1):
			icon = repeat_all_icon
			text = "Repeat All"
		elif (type == 2):
			icon = repeat_single_icon
			text = "Repeat One"
		
		# Load custom characters
		self.lcd.lcd_load_custom_chars(icon)
		
		# Show first part of icon
		self.display_data[1] = chr(0) + chr(1)
		
		# Show second part of icon
		self.display_data[2] = chr(2) + chr(3)
		
		# We need to center the text so we have to calculate how much spaces depending on screen width
		temp = self.columns - 2 - len(text) # 2 (for icon) and length of text
		
		# Add spaces from left side
		if ((temp % 2) != 0):
			lside = (temp / 2) + 1
		else:
			lside = (temp / 2)
			
		for i in range(lside):
			self.display_data[1] += ' '
			
		# Add the text
		self.display_data[1] += text
		
		# Add spaces from right side
		for i in range(temp / 2):
			self.display_data[1] += ' '
			
		# Now it's time for second row, check if shuffle is enabled or disabled:
		if (state == True):
			temp_text = "ENABLED"
		else:
			temp_text = "DISABLED"
			
		# We need to center the text so we have to calculate how much spaces depending on screen width
		temp = self.columns - 2 - len(temp_text) # 2 (for icon) and length of "Enabled" or "Disabled"
		
		# Add spaces from left side			
		for i in range(temp / 2):
			self.display_data[2] += ' '
			
		# Add the text
		self.display_data[2] += temp_text
		
		# Add spaces from right side
		if ((temp % 2) != 0):
			rside = (temp / 2) + 1
		else:
			rside = (temp / 2)
			
		for i in range(rside):
			self.display_data[2] += ' '
			
		# We will leave first line empty for now
		self.display_data[0] = ''
		for i in range(self.columns):
			self.display_data[0] += ' '
		
		# We will leave forth line empty for now
		self.display_data[3] = ''
		for i in range(self.columns):
			self.display_data[3] += ' '
			
		# At the end, update the display
		self.update_display()
			
	# Screen 0 shows artist and song name, times and track info
	def screen_0(self):
		data_changed = False
	
		# FIRST ROW: Get artist data from MPD and pass it to scroll function
		temp = self.scroll_row(0, self.mpd.get_data()['artist'])
		
		# Check if data has changed
		if (temp != self.display_data[0]):
			self.display_data[0] = temp
			data_changed = True
		
		# SECOND ROW: Get song name data from MPD and pass it to scroll function
		temp = self.scroll_row(1, self.mpd.get_data()['song'])
		
		# Check if data has changed
		if (temp != self.display_data[1]):
			self.display_data[1] = temp
			data_changed = True