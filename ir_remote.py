import os, threading, time

# Instance of this class will receive commands from IR remote via pipeline
class remote:
	# Class constructor, received pipeline name (path)
	def __init__(self, ir_pipe_path):
		self.pipe = ir_pipe_path
		
		# If FIFO pipe doesn't exists, create it
		if not os.path.exists(ir_pipe_path):
			os.mkfifo(ir_pipe_path)
			
		# Initialize display client
		self.display = False
		
		# No thread currently
		self.ir_t = False
		
	# Register display client so this thread can send commands to it
	def register_display(self, display):
		self.display = display
		
	# Main thread
	def remote_thread(self):
		pipe_fd = os.open(self.pipe, os.O_RDONLY) # Open pipe
		with os.fdopen(pipe_fd) as pipe:
			# Read messages every 10 ms
			while True:
				message = pipe.read().strip() # Read message from pipe
				if message:
					print message
					# Change display mode
					if (message == 'KEY_ENTER'):
						if (self.display != False):
							self.display.change_screen()
				time.sleep(0.01)
				
	# Start main remote thread
	def start(self):
		self.ir_t = threading.Thread(target=self.remote_thread, args = ()) # Create thread for updating LCD
		self.ir_t.daemon = True # Yep, it's a daemon, when main thread finish, this one will finish too
		self.ir_t.start() # Start it!
	
	# Function for waiting the thread to finish
	def join(self):
		if (self.ir_t != False):
			self.ir_t.join()
		