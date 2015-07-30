''' I2C_DISPLAY - Inerits display class from display.py '''

'''
Found on http://www.recantha.co.uk/blog/?p=4849
Compiled, mashed and generally mutilated 2014-2015 by Denis Pleic
Made available under GNU GENERAL PUBLIC LICENSE
Hacked about by Ken Robson (Hairybiker)
Modified and integrated into this script by Randy Cupic (XploD)
'''

# WARNING: For all overrided methods see display.py for documentation

import display, smbus
from time import *

''' COMMANDS FOR LCD DISPLAY '''
# Commands
LCD_CLEARDISPLAY = 0x01
LCD_RETURNHOME = 0x02
LCD_ENTRYMODESET = 0x04
LCD_DISPLAYCONTROL = 0x08
LCD_CURSORSHIFT = 0x10
LCD_FUNCTIONSET = 0x20
LCD_SETCGRAMADDR = 0x40
LCD_SETDDRAMADDR = 0x80

# Flags for display entry mode
LCD_ENTRYRIGHT = 0x00
LCD_ENTRYLEFT = 0x02
LCD_ENTRYSHIFTINCREMENT = 0x01
LCD_ENTRYSHIFTDECREMENT = 0x00

# Flags for display on/off control
LCD_DISPLAYON = 0x04
LCD_DISPLAYOFF = 0x00
LCD_CURSORON = 0x02
LCD_CURSOROFF = 0x00
LCD_BLINKON = 0x01
LCD_BLINKOFF = 0x00

# Flags for display/cursor shift
LCD_DISPLAYMOVE = 0x08
LCD_CURSORMOVE = 0x00
LCD_MOVERIGHT = 0x04
LCD_MOVELEFT = 0x00

# Flags for function set
LCD_8BITMODE = 0x10
LCD_4BITMODE = 0x00
LCD_2LINE = 0x08
LCD_1LINE = 0x00
LCD_5x10DOTS = 0x04
LCD_5x8DOTS = 0x00

# Define LCD device constants
LCD_WIDTH = 20    # Default characters per line # TODO
LCD_CHR = True
LCD_CMD = False

LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
LCD_LINE_3 = 0x94 # LCD RAM address for the 3rd line
LCD_LINE_4 = 0xD4 # LCD RAM address for the 4th line

# Flags for backlight control
LCD_BACKLIGHT = 0x08
LCD_NOBACKLIGHT = 0x00

# Control bits
En = 0b00000100 # Enable bit
Rw = 0b00000010 # Read/Write bit
Rs = 0b00000001 # Register select bit

# This class is used to communicate with LCD display connected via I2C
class i2c_device:
	# Initialize I2C device, receives address and port (optional)
	def __init__(self, addr, port=1):
		self.addr = addr
		self.bus = smbus.SMBus(port)

	# Write a single command
	def write_cmd(self, cmd):
		self.bus.write_byte(self.addr, cmd)
		sleep(0.0001) # Let it sleep for a while

	# Write a command and argument
	def write_cmd_arg(self, cmd, data):
		self.bus.write_byte_data(self.addr, cmd, data)
		sleep(0.0001)

	# Write a block of data
	def write_block_data(self, cmd, data):
		self.bus.write_block_data(self.addr, cmd, data)
		sleep(0.0001)
	

class i2c_display(display.display):
	# Method for LCD initialization
	''' OVERRIDED FROM DISPLAY '''
	def lcd_initialize(self):		
		# Initialize I2C_Device
		self.lcd_device = i2c_device(self.address)
		
		self.lcd_write(0x03)
		self.lcd_write(0x03)
		self.lcd_write(0x03)
		self.lcd_write(0x02)

		self.lcd_write(LCD_FUNCTIONSET | LCD_2LINE | LCD_5x8DOTS | LCD_4BITMODE)
		self.lcd_write(LCD_DISPLAYCONTROL | LCD_DISPLAYON)
		self.lcd_write(LCD_CLEARDISPLAY)
		self.lcd_write(LCD_ENTRYMODESET | LCD_ENTRYLEFT)

		self._displaycontrol = LCD_DISPLAYCONTROL | LCD_DISPLAYON | LCD_CURSORON | LCD_BLINKON

		sleep(0.2)
		
	# Toggle backlight on/off (State == True -> ON, State == False -> OFF)
	''' OVERRIDED FROM DISPLAY '''
	def lcd_backlight(self, state):
		if state == True:
			self.lcd_device.write_cmd(LCD_BACKLIGHT)
		elif state == False:
			self.lcd_device.write_cmd(LCD_NOBACKLIGHT)
		
	# Clocks EN to latch command
	def lcd_strobe(self, data):
		self.lcd_device.write_cmd(data | En | LCD_BACKLIGHT)
		sleep(.0005)
		self.lcd_device.write_cmd(((data & ~En) | LCD_BACKLIGHT))
		sleep(.0001)
	
	# Write four bits to LCD
	def lcd_write_four_bits(self, data):
		self.lcd_device.write_cmd(data | LCD_BACKLIGHT)
		self.lcd_strobe(data)

	# Write a command to lcd
	def lcd_write(self, cmd, mode=0):
		self.lcd_write_four_bits(mode | (cmd & 0xF0))
		self.lcd_write_four_bits(mode | ((cmd << 4) & 0xF0))
		
	# Write a character to LCD (or character ROM)
	def lcd_write_char(self, charvalue, mode=1):
		self.lcd_write_four_bits(mode | (charvalue & 0xF0))
		self.lcd_write_four_bits(mode | ((charvalue << 4) & 0xF0))
	
	# Write whole message to LCD - uses \n as new line !!
	''' OVERRIDED FROM DISPLAY '''
	def lcd_message(self, text):
		count = 1
		self.lcd_write(LCD_LINE_1)
		
		# Iterate through all chars in message
		for char in text:
			# Check if char is \n -> go to new line
			if char == '\n':
				if (count == 1 and self.rows >= 2):
					self.lcd_write(LCD_LINE_2)
				elif (count == 2 and self.rows >= 3):
					self.lcd_write(LCD_LINE_3)
				elif (count == 3 and self.rows >= 4):
					self.lcd_write(LCD_LINE_4)
				count = count + 1
			else:
				self.lcd_write_char(ord(char))
				
	# Load custom characters into display CGRAM (0 - 7)
	''' OVERRIDED FROM DISPLAY '''
	def lcd_load_custom_chars(self, fontdata):
		self.lcd_write(0x40);
		for char in fontdata:
			for line in char:
				self.lcd_write_char(line)   