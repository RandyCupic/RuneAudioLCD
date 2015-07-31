import time, math, threading, abc

class display:
	__metaclass__ = abc.ABCMeta

	# Class constructor, receives I2C address of display (usually it's 0x27, check with i2cdetect)
	# Also, number of rows and columns (for example, 2x16 or 4x20 LCD)
	def __init__(self, address, rows, columns, temp_screen_period, scroll_period):
		self.address = address
		self.rows = rows
		self.columns = columns
		
		# Default update time (period)
		self.period = 0.01 # s
		
		# Initialize LCD
		self.lcd_initialize()
		
		# Unlock the display; this variable is used to prevent multiple write to display
		self.lock_display = False
		
		# Temporary screen period (volume, repeat, shuffle...)
		self.temporary_screen_period = temp_screen_period / self.period # We have to divide it with period
		
		# Scroll period
		self.scroll_period = scroll_period / self.period # We have to divide it with period
		
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
		
		# Number of screens
		self.screens = 2
		
		# Initially, there's no temporary screen (like volume)
		self.temporary_screen = False
		
		# Current wait time for display
		self.wait_time = 0
		
		# Initially, we don't have to show volume screen
		self.volume_screen = False
		self.volume_value = 0
		
		# Also, we don't have to show play mode screen
		self.play_mode_screen = False
		self.play_mode_type = 0
		self.play_mode_state = False
		
		# Initially, data didn't changed
		self.data_changed = False
		self.time_changed = False
		
		# We don't have enough space for custom characters so we have to load them when needed
		# But it takes resources so we will load them into LCD only if needed
		# This variable contains currently loaded characters:
		# 0 - play/pause/stop icons
		# 1 - volume
		# 2 - shuffle
		# 3 - repeat all
		# 4 - repeat single
		self.current_custom_chars = -1 # Initially we want it to load something
		
	''' LCD METHODS '''
	# These methods are abstract; if you want to use any other library to write to LCD
	# Just inherit this display class and implement (override) these methods
	
	''' ABSTRACT METHOD, YOU HAVE TO IMPLEMENT IT IN INHERITED CLASS '''
	@abc.abstractmethod
	def lcd_initialize(self):
		# This method initializes the display
		# It MUST return LCD instance!!
		return
	
	''' ABSTRACT METHOD, YOU HAVE TO IMPLEMENT IT IN INHERITED CLASS '''
	@abc.abstractmethod
	def lcd_backlight(self, state):
		# This method turns on and off LCD backlight
		# It receives True or False
		return
	
	''' ABSTRACT METHOD, YOU HAVE TO IMPLEMENT IT IN INHERITED CLASS '''
	@abc.abstractmethod
	def lcd_message(self, message):
		# This method writes the whole message to the LCD display
		# To go to the new line, it uses "\n" character
		return
	
	''' ABSTRACT METHOD, YOU HAVE TO IMPLEMENT IT IN INHERITED CLASS '''	
	@abc.abstractmethod
	def lcd_load_custom_chars(self, data): 
		# This method loads custom characters in LCD display
		# It receives an array with data for each custom character
		# Each array item contains 8 values for each line in one box
		''' EXAMPLE '''
		''' data = [
				[ 0b00000, 0b11111, 0b11111, 0b11111, 0b11111, 0b11111, 0b11111, 0b00000 ],
				[ 0b00000, 0b01000, 0b01100, 0b01110, 0b01110, 0b01100, 0b01000, 0b00000 ],
				[ 0b00000, 0b01010, 0b01010, 0b01010, 0b01010, 0b01010, 0b01010, 0b00000 ]
		] '''
		# This will load 3 custom characters (stop, play, pause icons) on places 0-2
		return
		
	# We need to register MPD client to be able to retrieve data from it
	def register(self, mpd):
		self.mpd = mpd
		
	# Function for updating LCD display
	def update_display(self):
		tmp = '';
		# Iterate through all lines
		for i in range(self.rows):
			tmp = tmp + self.display_data[i];
			if (i != (self.rows - 1)):
				tmp = tmp + '\n';

		self.lcd_message(tmp);
			
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
		temp = self.scroll[row]['data'][self.scroll[row]['position']:self.scroll[row]['position']+self.columns]
		
		# If direction is FORWARDS
		if (self.scroll[row]['direction'] == 0):
			# If we've reached the end, let us go backwards (change direction)
			if (self.scroll[row]['position'] == (len(self.scroll[row]['data']) - self.columns)):
				self.scroll[row]['direction'] = 1 # Set direction to backwards
			else:
				self.scroll[row]['position'] = self.scroll[row]['position'] + 1 # Move to next position
				
		# If direction is BACKWARDS
		if (self.scroll[row]['direction'] == 1):
			# If we've reached the beginning, let us go forwards (change direction)
			if (self.scroll[row]['position'] == 0):
				self.scroll[row]['direction'] = 0 # Set direction to forwards
			else:
				self.scroll[row]['position'] = self.scroll[row]['position'] - 1 # Move to next position
				
		return temp
		
	# Function for showing volume screen
	def show_volume(self):		
		# Speaker icon custom characters
		speaker_icon = [ 
				[ 0b00000, 0b00000, 0b00000, 0b00000, 0b11111, 0b10001, 0b10001, 0b10001 ],
				[ 0b00001, 0b00011, 0b00101, 0b01001, 0b10001, 0b00001, 0b00001, 0b00001 ],
				[ 0b10001, 0b10001, 0b10001, 0b11111, 0b00000, 0b00000, 0b00000, 0b00000 ],
				[ 0b00001, 0b00001, 0b00001, 0b10001, 0b01001, 0b00101, 0b00011, 0b00001 ]
		]
		
		# If display is 4x20, this will be displayed in lines 2 and 3, otherwise 1 and 2 (2x16)
		if (self.rows >= 4):
			skip_lines = 1
		else:
			skip_lines = 0
		
		# Load custom characters if needed
		if (self.current_custom_chars != 1):
			self.lcd_load_custom_chars(speaker_icon)
			self.current_custom_chars = 1
		
		# Show first part of icon + "volume"
		self.display_data[skip_lines] = chr(0) + chr(1) + ' Volume'
		
		# Show second part of icon
		self.display_data[skip_lines + 1] = chr(2) + chr(3) + ' '
		
		# If volume is 0 or 100 ...
		if (self.volume_value == 0 or self.volume_value == 100):
			# Fill spaces between; columns - 3 (2 for icon + space) - 12 (length of 'VolumeMIN' or 'VolumeMAX')
			for i in range(self.columns - 12):
				self.display_data[skip_lines] += ' '
		
		# If volume is 0, show minimum and no blocks in third line
		if (self.volume_value == 0):
			self.display_data[skip_lines] += 'MIN'
			for i in range(self.columns - 3): # -3 for icon (2) and space
				self.display_data[skip_lines + 1] += ' '
		
		# If volume is 100, show maximum and all blocks in third line	
		elif (self.volume_value == 100):
			self.display_data[skip_lines] += 'MAX'
			for i in range(self.columns - 3):
				self.display_data[skip_lines + 1] += chr(255)
		
		# Else, show value in % and the corresponding number of blocks
		else:
			# Fill spaces between; columns - 3 (icon + space) - 10 (length of 'VolumeXX %)
			for i in range(self.columns - 13):
				self.display_data[skip_lines] += ' '
		
			# Check if there is only one digit and append another space
			if (self.volume_value < 10):
				self.display_data[skip_lines] += ' '
			
			# Append volume value
			self.display_data[skip_lines] += `self.volume_value` + ' %'
			
			# Calculate number of blocks to show
			temp = (self.volume_value / int(math.ceil((100.0 / (self.columns - 3))))) + 1
			
			# Append the blocks
			for i in range (temp):
				self.display_data[skip_lines + 1] += chr(255)
				
			# Fill remaining space with ' '
			for i in range (self.columns - temp - 3):
				self.display_data[skip_lines + 1] += ' '
			
		# If display is 4x20, we will leave first and forth line empty for now
		if (self.rows >= 4):
			self.display_data[0] = ''
			for i in range(self.columns):
				self.display_data[0] += ' '
		
			self.display_data[3] = ''
			for i in range(self.columns):
				self.display_data[3] += ' '
			
		# At the end, update the display
		while (self.lock_display):
			pass
		self.lock_display = True
		self.update_display()
		self.lock_display = False
		
	# Function for showing shuffle (0), repeat all (1) or repeat single (2) screen
	def show_play_mode(self):		
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
		
		# If display is 4x20, this will be displayed in lines 2 and 3, otherwise 1 and 2 (2x16)
		if (self.rows >= 4):
			skip_lines = 1
		else:
			skip_lines = 0
		
		# Choose icon and text, according to type
		if (self.play_mode_type == 0):
			icon = shuffle_icon
			text = "Shuffle Mode"
		elif (self.play_mode_type == 1):
			icon = repeat_all_icon
			text = "Repeat All"
		elif (self.play_mode_type == 2):
			icon = repeat_single_icon
			text = "Repeat One"
		
		# Load custom characters if needed
		if (self.current_custom_chars != (self.play_mode_type + 2)):
			self.lcd_load_custom_chars(icon)
			self.current_custom_chars = (self.play_mode_type + 2)
		
		# Show first part of icon
		self.display_data[skip_lines] = chr(0) + chr(1)
		
		# Show second part of icon
		self.display_data[skip_lines + 1] = chr(2) + chr(3)
		
		# We need to center the text so we have to calculate how much spaces depending on screen width
		temp = self.columns - 2 - len(text) # 2 (for icon) and length of text
		
		# Add spaces from left side
		if ((temp % 2) != 0):
			lside = (temp / 2) + 1
		else:
			lside = (temp / 2)
			
		for i in range(lside):
			self.display_data[skip_lines] += ' '
			
		# Add the text
		self.display_data[skip_lines] += text
		
		# Add spaces from right side
		for i in range(temp / 2):
			self.display_data[skip_lines] += ' '
			
		# Now it's time for second row, check if shuffle is enabled or disabled:
		if (self.play_mode_state == True):
			temp_text = "ENABLED"
		else:
			temp_text = "DISABLED"
			
		# We need to center the text so we have to calculate how much spaces depending on screen width
		temp = self.columns - 2 - len(temp_text) # 2 (for icon) and length of "Enabled" or "Disabled"
		
		# Add spaces from left side			
		for i in range(temp / 2):
			self.display_data[skip_lines + 1] += ' '
			
		# Add the text
		self.display_data[skip_lines + 1] += temp_text
		
		# Add spaces from right side
		if ((temp % 2) != 0):
			rside = (temp / 2) + 1
		else:
			rside = (temp / 2)
			
		for i in range(rside):
			self.display_data[skip_lines + 1] += ' '
		
		# If display is 4x20 ...
		if (self.rows >= 4):
			# We will leave first line empty for now
			self.display_data[0] = ''
			for i in range(self.columns):
				self.display_data[0] += ' '
			
			# We will leave forth line empty for now
			self.display_data[3] = ''
			for i in range(self.columns):
				self.display_data[3] += ' '
			
		# At the end, update the display
		while (self.lock_display):
			pass
		self.lock_display = True
		self.update_display()
		self.lock_display = False
		
	# This function is called by MPD when volume is changed
	def volume_changed(self, value):
		# We only have to notify the display thread
		self.volume_value = value
		self.volume_screen = True
		
	# This function is called by MPD when play mode is changed
	def play_mode_changed(self, type, state):
		# We only have to notify the display thread
		self.play_mode_type = type
		self.play_mode_state = state
		self.play_mode_screen = True
		
	# This function is called by MPD when data changes (for example, song)
	def data_change(self):
		self.data_changed = True
	
	# This function is called by MPD when time changes (for example, second passed in elapsed time)
	def time_change(self):
		self.time_changed = True
		
	# This function is called by remote or button to change screen mode
	def change_screen(self):
		# For 4x20 display, jump by 2, for 2x16 by 1
		if (self.rows >= 4):
			self.screen += 2
		else:
			self.screen += 1
			
		# If we reached the end, let's go from beginning
		if (self.screen >= self.screens):
			self.screen = 0
		
	# Convert seconds to M:S (type = 0), H:M:S (type = 1) or D:H:M:S (type = 2)
	def convert_time(self, seconds, type):
		# Initialize
		sec = 0
		min = 0
		hour = 0
		day = 0
	
		# In any type, we need seconds
		sec = seconds % 60;
		
		# M:S type, get seconds
		if (type == 0):
			min = int( int(seconds) / 60 )
		
		# H:M:S type, get hours and seconds
		elif (type == 1):
			min = int( int(seconds) / 60 ) % 60
			hour = int( int(seconds) / 3600 )
		
		# D:H:M:S type, get days, hours and seconds
		elif (type == 2):
			min = int( int(seconds) / 60 ) % 60
			hour = int( int(seconds) / 3600 ) % 24
			day = int ( int(seconds) / 86400 )
			
		temp = ''
		
		# Create string to return
		if (sec < 10):
			temp += '0' + `sec`
		else:
			temp += `sec`
			
		if (min < 10):
			temp = '0' + `min` + ':' + temp
		else:
			temp = `min` + ':' + temp
			
		if (type == 1):
			if (hour < 10):
				temp = '0' + `hour` + ':' + temp
			else:
				temp = `hour` + ':' + temp
				
		if (type == 2):
			temp = `day` + 'd ' + temp

				
		return temp
			
	# Screen 0 shows artist and song name, times and track info
	# Returns whether the data has changed or not
	def screen_0(self):
		data_changed = False
	
		# FIRST ROW: Get artist data from MPD and pass it to scroll function
		try:
			temp = self.scroll_row(0, self.mpd.getData()['artist'])
		except KeyError:
			temp = ''
		
		# Check if data has changed
		if (temp != self.display_data[0]):
			self.display_data[0] = temp
			data_changed = True
		
		# SECOND ROW: Get song name data from MPD and pass it to scroll function
		try:
			temp = self.scroll_row(1, self.mpd.getData()['title'])
		except KeyError:
			temp = ''
		
		# Check if data has changed
		if (temp != self.display_data[1]):
			self.display_data[1] = temp
			data_changed = True
			
		return data_changed
		
	# This screen shows time and track/station info
	# Returns whether the data has changed or not
	def screen_1(self):
		data_changed = False
	
		# Play/pause/stop icons
		state_icons = [
				[ 0b00000, 0b11111, 0b11111, 0b11111, 0b11111, 0b11111, 0b11111, 0b00000 ],
				[ 0b00000, 0b01000, 0b01100, 0b01110, 0b01110, 0b01100, 0b01000, 0b00000 ],
				[ 0b00000, 0b01010, 0b01010, 0b01010, 0b01010, 0b01010, 0b01010, 0b00000 ]
		]
	
		temp = ''
		
		# If display is 4x20, this will be displayed in lines 3 and 4, otherwise 1 and 2 (2x16)
		if (self.rows >= 4):
			skip_lines = 2
		else:
			skip_lines = 0
			
		# If file is playing
		if (self.mpd.getData()['type'] == 0):
			# Get elapsed time
			elapsed_time = self.convert_time(self.mpd.getData()['elapsed_time'], 0)
			
			# Get total track time
			total_time = self.convert_time(self.mpd.getData()['total_time'], 0)
			
			# Get state icon
			icon = chr(self.mpd.getData()['state'])
			
			temp = ''
			
			# Show elapsed_time
			temp += elapsed_time
			
			# We have to center the icon so we have to count how much spaces to put
			space_count = (self.columns - len(elapsed_time) - len(total_time) - 1) # -1 is for icon
			
			# We have to be careful for numbers not dividable by 2
			if ((space_count % 2) != 0):
				i = space_count / 2 + 1
			else:
				i = space_count / 2
				
			# Fill spaces
			for j in range(space_count / 2):
				temp += ' '
				
			# Show icon
			temp += icon
			
			# Fill remaining spaces
			for j in range (i):
				temp += ' '
				
			# Show total time
			temp += total_time
			
		# else if radio is playing
		elif (self.mpd.getData()['type'] == 1):		
			# Get elapsed time
			elapsed_time = self.convert_time(self.mpd.getData()['elapsed_time'], 1)
			
			# Get state icon
			icon = chr(self.mpd.getData()['state'])
			
			temp = ''
			
			# Show elapsed_time
			temp += elapsed_time
			
			# Show something instead total time
			if (self.columns >= 20):
				word = 'STREAMING'
			else:
				word = 'STREAM'
			
			# We have to center the icon so we have to count how much spaces to put
			space_count = (self.columns - len(elapsed_time) - len(word) - 1) # -1 is for icon, -6 is for length of 'STREAM'
			
			# We have to be careful for numbers not dividable by 2
			if ((space_count % 2) != 0):
				i = space_count / 2 + 1
			else:
				i = space_count / 2
				
			# Fill spaces
			for j in range(space_count / 2):
				temp += ' '
				
			# Show icon
			temp += icon
			
			# Fill remaining spaces
			for j in range (i):
				temp += ' '
				
			# Show the word
			temp += word
			
		# Check if data has changed
		if (temp != self.display_data[skip_lines]):
			self.display_data[skip_lines] = temp
			data_changed = True
			
		# Last line shows RADIO/FILE and bitrate
		if (self.mpd.getData()['type'] == 0):
			word = "FILE"
			
		elif (self.mpd.getData()['type'] == 1):
			word = "RADIO"
		
		# Get bitrate
		bitrate = `self.mpd.getData()['bitrate']` + ' kbps'
		
		# Show type
		temp = word
		
		# Between word and bitrate we will fill spaces
		for i in range(self.columns - len(word) - len(bitrate)):
			temp += ' '
			
		# Show bitrate
		temp += bitrate
		
		# Check if data has changed
		if (temp != self.display_data[skip_lines + 1]):
			self.display_data[skip_lines + 1] = temp
			data_changed = True
			
		# If data changed, see if there's a need to load custom charachters
		if (data_changed):
			# Load custom characters, if needed
			if (self.current_custom_chars != 0):
				self.lcd_load_custom_chars(state_icons)
				self.current_custom_chars = 0
		
		return data_changed
			
	# Main function which is running all the time to update display
	def main_function(self):
		while True:
			# Set period for checking for changes
			time.sleep(self.period)
			
			# Check if volume is set
			if (self.volume_screen):
				self.volume_screen = False
				self.show_volume()
				self.wait_time = self.temporary_screen_period
				self.temporary_screen = True
				
			# Check if play mode is set
			if (self.play_mode_screen):
				self.play_mode_screen = False
				self.show_play_mode()
				self.wait_time = self.temporary_screen_period
				self.temporary_screen = True
				
			# Check if data changed - time to update display
			if (self.data_changed):
				self.data_changed = False
				self.wait_time = 0 # Skip waiting
				
			# Check if time has changed
			if (self.time_changed):
				self.time_changed = False
				
				# If there's a temporary screen (volume), we don't want to interrupt it by clock
				if (self.temporary_screen == False):
					self.wait_time = 0
			
			# Check if there's a wait time to pass
			if (self.wait_time > 0):
				self.wait_time -= 1
				continue
			
			# Temporary screen passed
			self.temporary_screen = False
			
			data_changed = False
			
			# If screen 0 is selected
			if (self.screen == 0):
				# If display is 4x20
				if (self.rows >= 4):
					data_changed1 = self.screen_0()
					data_changed2 = self.screen_1()
					data_changed = data_changed1 or data_changed2
					
				# Else it's a 2x16
				else:
					data_changed = self.screen_0()
					
			# Else if screen is 1
			elif (self.screen == 1):
				# 1 is only for 2x16 display
				if (self.rows < 4):
					data_changed = self.screen_1()
					
				# Else return to screen 0
				else:
					self.screen == 0
			
			# If data has changed, update display
			if (data_changed):					
				while (self.lock_display):
					continue
				
				self.lock_display = True
				self.update_display()
				self.lock_display = False
				
				data_changed = False
				
			self.wait_time = self.scroll_period
				
	# Function for starting display thread
	def start(self):
		self.lcd_t = threading.Thread(target=self.main_function, args = ()) # Create thread for updating LCD
		self.lcd_t.daemon = True # Yep, it's a daemon, when main thread finish, this one will finish too
		self.lcd_t.start() # Start it!
	
	# Function for waiting the thread to finish
	def join(self):
		self.lcd_t.join()