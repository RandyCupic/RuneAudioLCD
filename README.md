# RuneAudioLCD
Small script written in Python for RuneAudio project (www.RuneAudio.com) running on Raspberry Pi 1/2 computer, which displays all neccessary info on a LCD display and which uses hardware buttons and IR remote controller to control playback and system.

## Features
### Display features
- can be turned off (to only use buttons and/or remote)
- support for 20x4 and 16x2 displays connected via I2C
- 3 different screens for 20x4 LCD, 6 for 16x2 LCD respectively
- current song and artist info, with scrolling
- elapsed time and song duration, with listened percentage (only for local files)
- play, pause or stop icon
- shows wheter it's playing radio or file, with bitrate in kbps
- shows volume, random, repeat and single status, on change
- Ethernet and Wi-Fi IP address, if connected
- system uptime, and music play time
- current date and time, CPU temperature and RAM usage (used/total)

### Button features
- can be turned off (to only use display and/or remote)
- play/pause, volume up/down, previous, next and stop buttons
- each button can be turned on/off (possibility of using only some of listed buttons)

### IR remote features
- can be turned off (to only use display and/or buttons)
- power off and reboot options
- play, pause, volume up/down, previous, next and stop options
- repeat, single, shuffle options
- switch through different screens (display modes)
- turn on/off LCD backlight

## Requirements
- Raspberry Pi 1/2 computer running RuneAudio distribution based on modified Archlinux (from www.RuneAudio.com)
- 16x2 or 20x4 I2C LCD display (not neccesarry)
- up to 5 hardware push buttons (not neccessarry)
- IR receiver (not neccessarry)
- installed Python2 compiler
- installed and working LIRC (required for IR remote to work)
- script for IR remote which sends required strings via pipeline on button presses
