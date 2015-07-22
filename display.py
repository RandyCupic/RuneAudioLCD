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
		
	# We need to register MPD client to be able to retrieve data from it
	def register_mpd(self, mpd):
		self.mpd = mpd
		
	# Function for updating LCD display
	def update_display(self):
		tmp = '';
		# Iterate through all lines
		for i in range(1, self.rows + 1):
			tmp = tmp + self.display_data[i-1];
			if (i != self.rows):
				tmp = tmp + '\n';
		
		print tmp;
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
		if (len(text) == self.columns:
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
		self.volume_changed = True # We have to notify the thread to stop it from replacing the screen
		
		self.display_data[0] = 'Volume'
		
		# If volume is 0 or 100 ...
		if (volume == 0 or volume == 100):
			# Fill spaces between; columns - length of 'VolumeMINIMUM' or 'VolumeMAXIMUM'
			for i in range(self.columns - 13):
				self.display_data[0] += ' '
		
		# If volume is 0, show minimum and no blocks in third line
		if (volume == 0):
			self.display_data[0] += 'MINIMUM'
			self.display_data[2] = ''
			for i in range(self.columns):
				self.display_data[2] += ' '
		
		# If volume is 100, show maximum and all blocks in third line	
		elif (volume == 100):
			self.display_data[0] += 'MAXIMUM'
			self.display_data[2] = ''
			for i in range(self.columns):
				self.display_data[2] += chr(255)
		
		# Else, show value in % and the corresponding number of blocks
		else:
			# Fill spaces between; columns - length of 'VolumeXX %'
			for i in range(self.columns - 10):
				self.display_data[0] += ' '
		
			# Check if there is only one digit and append another space
			if (volume < 10):
				self.display_data[0] += ' '
			
			# Append volume value
			self.display_data[0] += `volume` + ' %'
			
			self.display_data[2] = ''
			
			# Calculate number of blocks to show
			temp = (volume / int(math.ceil((100 / self.columns)))) + 1
			
			# Append the blocks
			for i in range (0,pom_num):
				self.display_data[2] += chr(255)
			
		# We will leave second line empty for now
		for i in range(self.columns):
			self.display_data[1] += ' '
		
		# We will leave forth line empty for now
		for i in range(self.columns):
			self.display_data[3] += ' '
			
	# Screen 0 shows artist and song name, times and track info
	def screen_0(self):
		