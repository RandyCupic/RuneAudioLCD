import i2c_display, mpd_client, ir_remote, time

#########  MPD PARAMETERS  ##############
# Only if you know what you're doing! 	#
HOST = 'localhost'						#
PORT = '6600'							#
PASSWORD = False						#
CON_ID = {'host':HOST, 'port':PORT}		#
#########################################

display = i2c_display.i2c_display(0x27, 2, 16, 5, 0.1);
mpdcl = mpd_client.mpd_client(CON_ID, PASSWORD)
remote = ir_remote.remote("/tmp/irpipe")

display.register(mpdcl)
mpdcl.register(display)
remote.register_display(display)
display.start()
remote.start()
mpdcl.mpdMain()

print "test"

'''display.start()

time.sleep(5)

display.volume_changed(65)

time.sleep(3)

display.play_mode_changed(1, True)

time.sleep(2)

display.play_mode_changed(2, False)

time.sleep(8)

display.play_mode_changed(0, True)'''


#display.join()