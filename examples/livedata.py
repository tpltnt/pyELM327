#! /usr/bin/python

import time, sys
sys.path.append(".")
sys.path.append("..")
from elm327 import elm327, pids

with elm327.ELM327('/dev/ttyUSB0', debug=0) as elm:
	# Attempt to set a higher baud. Note that this will, when the script is
	# stopped with CTRL+C, leave the ELM327 in a semi-usable state - it will
	# still be configured to use the higher baud rate!

	# So next time around you'll have to either initialize the ELM327 object
	# with baud=500000, or simply reset the device by unplugging it and
	# plugging it back in. Or, simply comment this line out, because at the
	# time of writing we don't run out of bandwidth for the speed we're
	# polling the PIDs at.
	#elm.tryBaudrate(500000)

	print("Device reports as: %s @ %d bps" % (elm.id, elm.baudrate))

	supported = elm.fetchSupportedPIDsLive()
	if supported == None:
		elm.write('ATZ')
		exit()

	while True:
		print("\033[6;3H")
		# Iteratively fetch all PIDs in Mode 01
		for spid in supported:
			pid = int(spid, 16)
			try:
				res = elm.fetchLiveData(pid)
				if res:
					print("%s: %s %s" % (res['name'], res['value'], res['units']))
			except Exception as e:
				if e == 'STOPPED':
					elm.reset(1) # warm reset, keep baud rate.
					time.sleep(1) # wait 1 second before trying again.
				else:
					print(e)
