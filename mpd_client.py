from mpd import (MPDClient, CommandError)
import threading, time, math

class mpd_client:
	def __init__(self, con_id, password):
		# Create First MPD client(for status)
		self.client = MPDClient()
		
		# Create Second MPD client (for commands)
		self.cmd_client = MPDClient()
		
		# Connect to the MPD daemon (first client)
		if (self.mpdConnect(self.client, con_id) == False):
			print('Connection to MPD daemon (for status) failed!')
			sys.exit(1)
			
		# Connect to the MPD daemon (second client)
		if (self.mpdConnect(self.cmd_client, con_id) == False):
			print('Connection to MPD daemon (for commands) failed!')
			sys.exit(1)
			
		# If password is set, we have to authenticate
		if password:
			# First client
			if (self.mpdAuth(self.client, password) == False):
				print('MPD authentication (for status) failed!')
				sys.exit(1)
			
			# Second client
			if (self.mpdAuth(self.cmd_client, password) == False):
				print('MPD authentication (for commands) failed!')
				sys.exit(1)
				
		# MPD Ping Thread - we have to ping cmd_client to prevent closing connection		
		mpdping_t = threading.Thread(target=self.mpdPing, args = ()) # Create thread for pinging MPD
		mpdping_t.daemon = True # Yep, it's a daemon, when main thread finish, this one will finish too
		mpdping_t.start() # Start it!
		
		# Initialize data container
		self.data = {
			'artist': '', # Contains artist name or radio station name
			'title': '', # Contains song title or when radio playing, "artist - title" format
			'type': 0, # 0 - file, 1 - radio
			'state': 0, # 0 - stopped, 1 - playing, 2 - paused
			'volume': '', # Volume value
			'shuffle': False, # True - ON, False - OFF
			'repeat_all': False, # True - ON, False - OFF
			'repeat_single': False, # True - ON, False - OFF
			'elapsed_time': 0, # Song elapsed time
			'total_time': 0, # Total song duration
			'bitrate': 0, # Song/station bitrate (for example 320)
			'playtime': 0, # Total playing time from last reboot
			'uptime': 0 # Total uptime from last reboot
		}
			
		# Initialize LCD listener for changes
		self.LCD_client = False
		
		# Get first data update
		self.updateData()
	
	# Function for connecting to MPD daemon
	def mpdConnect(self, client, con_id):
		try:
			client.connect(**con_id)
		except SocketError:
			return False
		return True
		
	# Function for authenticating to MPD if password is set
	def mpdAuth(client, pwd):
		try:
			client.password(pwd)
		except CommandError:
			return False
		return True
		
	# Function for pinging cmd_client, we have to ping it or it will close connection
	def mpdPing(self):
		while True:
			time.sleep(50) # We will ping it every 50 seconds
			self.cmd_client.ping() # Ping it!
			
	# Register LCD client listener
	def register(self, lcd):
		self.LCD_client = lcd
			
	# Function for setting every first letter of word to uppercase
	def toUpper(self, data):
		#Declare list
		lst = []
		
		words = data.split(" ")
		
		# Iterate through words
		for word in words:
			# Check if there's a word
			if (len(word) == 0):
				continue
				
			# Check if first word is ( or -
			if ((word[0] == '(' or word[0] == '-')):
				if (len(word) >= 3):
					lst.append(word[0] + word[1].upper() + word[2:]) # Add to list
				elif (len(word) == 2):
					lst.append(word[0] + word[1].upper()) # Add to list
				else:
					lst.append(word[0]) # Add to list
				
			elif (len(word) >= 2):
				lst.append(word[0].upper() + word[1:]) # Add to list
			
			else:
				lst.append(word[0].upper()) # Add to list
				
		# Return joined list
		return " ".join(lst)
		
	# This function is called by buttons to give commands to MPD
	def commands(self, command):
		if (command == 'PLAY'):
			if (self.data['state'] == 1):
				self.cmd_client.pause(1)
			else:
				self.cmd_client.play()
				
		elif (command == 'STOP'):
			self.cmd_client.stop()
			
		elif (command == 'NEXT'):
			self.cmd_client.next()
			
		elif (command == 'PREV'):
			self.cmd_client.previous()
			
		elif (command == 'VDN'):
			# Get volume value
			vol = self.data['volume'] - 5
			
			if (vol < 0):
				vol = 0
			
			self.cmd_client.setvol(vol)
			
		elif (command == 'VUP'):
			# Get volume value
			vol = self.data['volume'] + 5
			
			if (vol > 100):
				vol = 100
			
			self.cmd_client.setvol(vol)
		
	# Function for updating data
	# Returns which option has been changed (shuffle - 0, repeat all - 1, repeat single - 2, nothing changed - -1)
	def updateData(self):
		# Nothing has changed so far
		changed = -1
		
		# Fetch volume
		try:
			self.data['volume'] = int(self.client.status()['volume'])
		except KeyError:
			self.data['volume'] = 0
			
		# Get state
		try:
			state = self.client.status()['state']
		except KeyError:
			state = ''
			
		# Get station
		try:
			station = self.client.currentsong()['name']
		except KeyError:
			station = ''
			
		# Get title
		try:
			title = self.client.currentsong()['title']
		except KeyError:
			title = ''

		# Get artist
		try:
			artist = self.client.currentsong()['artist']
		except KeyError:
			artist = ''
		
		# Check whether the player is playing, paused or stopped
		if (state == 'play'):
			self.data['state'] = 1

		elif (state == 'stop' or state == ''):
			self.data['state'] = 0
			
		elif (state == 'pause'):
			self.data['state'] = 2
		
		# Check if web radio is playing (radio station)
		if(station != ''):
			self.data['type'] = 1 # Set data type to radio
			
			# Get radio station name in artist field, all first letters to uppercase
			self.data['artist'] = self.toUpper(station)
			
			# Check if there is no data
			if (title == ''):
				self.data['title'] = '[Unknown Song]'
			
			# Else get artist - title in title field, all first letters to uppercase
			else:
				self.data['title'] = self.toUpper(title)
			
		# Else, it's a file playing
		else:
			self.data['type'] = 0 # Set data type to file
			
			# Check if there's no artist data
			if (artist == ''):
				self.data['artist'] = '[Unknown Artist]'
			
			# Else, get artist name, all first letters to uppercase
			else:
				self.data['artist'] = self.toUpper(artist)
				
			# Check if there's no song title data
			if (title == ''):
				self.data['title'] = '[Unknown Title]'
			
			# Else get current song title, all first letters to uppercase
			else:		
				self.data['title'] = self.toUpper(title)
				
		# If player is playing or it's paused, get elapsed time, total track time and bitrate
		if (self.data['state'] == 1 or self.data['state'] == 2):
			# If file is playing, get total track time
			if (self.data['type'] == 0):
				try:
					self.data['total_time'] = int(self.client.currentsong()['time'])
				except KeyError:
					self.data['total_time'] = 0
					
			# Else, if radio is playing, there's no total track time
			else:
				self.data['total_time'] = 0
			
			# Get elapsed time and convert it to seconds (int)
			try:
				self.data['elapsed_time'] = int(math.floor(float(self.client.status()['elapsed'])))
			except KeyError:
				self.data['elapsed_time'] = 0
				
			# Get track/station bitrate
			try:
				self.data['bitrate'] = int(self.client.status()['bitrate'])
			except KeyError:
				self.data['bitrate'] = 0
		
		# Else, put elapsed time to zero
		else:
			self.data['elapsed_time'] = 0		
		
		# Get total playtime and uptime from last reboot
		try:
			self.data['uptime'] = int(self.client.stats()['uptime'])
		except KeyError:
			self.data['uptime'] = 0
			
		try:
			self.data['playtime'] = int(self.client.stats()['playtime'])
		except KeyError:
			self.data['playtime'] = 0
		
		# Get shuffle state
		try:
			temp = self.client.status()['random']
			if (temp == '0'):
				temp = False
			elif (temp == '1'):
				temp = True
			
			# Check if shuffle has changed
			if (temp != self.data['shuffle']):
				changed = 0 # Shuffle has changed
				self.data['shuffle'] = temp # Update data
		except KeyError:
			pass
			
		# Get repeat all state
		try:
			temp = self.client.status()['repeat']
			if (temp == '0'):
				temp = False
			elif (temp == '1'):
				temp = True
			
			# Check if repeat all has changed
			if (temp != self.data['repeat_all']):
				changed = 1 # Repeat all has changed
				self.data['repeat_all'] = temp # Update data
		except KeyError:
			pass
			
		# Get repeat single state
		try:
			temp = self.client.status()['single']
			if (temp == '0'):
				temp = False
			elif (temp == '1'):
				temp = True
			
			# Check if repeat single has changed
			if (temp != self.data['repeat_single']):
				changed = 2 # Repeat single has changed
				self.data['repeat_single'] = temp # Update data
		except KeyError:
			pass
			
		# Return what has changed
		return changed
		
	# Function for counters (will be running in another thread)
	def timeCounter(self):
		while True:
			time.sleep(1) # Wait one second
			self.data['uptime'] += 1 # Increase uptime
			
			# If player is playing
			if (self.data['state'] == 1):
				self.data['elapsed_time'] += 1 # Increase elapsed time
				self.data['playtime'] += 1 # Increase total playtime
				
			# Time is changed, notify LCD thread
			self.LCD_client.time_change()
			
	# Function which returns data for LCD display to get it
	def getData(self):
		return self.data
			
	# Main function which is running in thread and waiting for changes
	def mpdMain(self):
		# Counter Thread - we have to count elapsed time, playtime and uptime
		self.counter_t = threading.Thread(target=self.timeCounter, args = ()) # Create thread
		self.counter_t.daemon = True # Yep, it's a daemon, when main thread finish, this one will finish too
		self.counter_t.start() # Start it!	
	
		while True:
			# Wait for any change from MPD
			self.client.send_idle()
			status = self.client.fetch_idle()
			
			# Update data
			changed = self.updateData()

			# Check if some option changed
			if (changed != -1):
				temp = False
				
				# Get changed option state
				if (changed == 0):
					# Shuffle changed
					temp = self.data['shuffle']
					
				elif (changed == 1):
					# Repeat all changed
					temp = self.data['repeat_all']
					
				elif (changed == 2):
					# Repeat single changed
					temp = self.data['repeat_single']
			
				self.LCD_client.play_mode_changed(changed, temp) # Notify LCD
			
			# Check what has changed
			try:
				type = status[0]
			except KeyError:
				continue
			
			# If volume has changed
			if (type == 'mixer'):
				self.LCD_client.volume_changed(self.data['volume'])
			
			# Else, if song or something from player changed
			elif (type == 'player'):
				self.LCD_client.data_change()
			
		# Wait for counter thread to finish
		self.counter_t.join()