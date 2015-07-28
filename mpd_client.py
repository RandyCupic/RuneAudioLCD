from mpd import (MPDClient, CommandError)
import threading, time

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
			'repeat_single': False, # True - ON, False - OFF
			'repeat_single': False, # True - ON, False - OFF
			'elapsed_time': 0, # Song elapsed time
			'total_time': 0, # Total song duration
			'bitrate': 0 # Song/station bitrate (for example 320)
		}
			
		volume = int(self.client.status()['volume']) # Get volume
		
		print volume
		
		print self.client.status()
	
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
			
	# Function for setting every first letter of word to uppercase
	def toUpper(self, data):
		#Declare list
		lst = []
		
		# Iterate through words
		for word in data:
			# Check if first word is ( or -
			if (word[0] == '(' or word[0] == '-'):
				lst.append(word[0] + word[1].upper() + word[2:]) # Add to list
				
			else:
				lst.append(word[0].upper() + word[1:]) # Add to list
				
		# Return joined list
		return " ".join(lst)
			
	# Function for updating data
	def updateData(self):
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
			title = client.currentsong()['title']
		except KeyError:
			title = ''

		# Get artist
		try:
			artist = client.currentsong()['artist']
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
			
	# Main function which is running in thread and waiting for changes
	def mpdMain(self):
		while True:
			# Wait for any change from MPD
			self.client.send_idle()
			status = self.client.fetch_idle()
			
			print status