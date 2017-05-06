#!/usr/bin/env python3

import time, sys
sys.path.append(".")
sys.path.append("..")
from elm327 import elm327, pids

with elm327.ELM327('/dev/ttyUSB0', debug=0) as elm:
	"""
	Hopefully will print all Diagnostic Trouble Codes stored on the ECU. Some 
	manufacturers are shady with this stuff so it doesn't always work.

	The fetchDTCs() function's output is subject to change, eventually it
	will return a list of the DTCs and it will be up to the caller to print.
	"""
	print(elm.fetchDTCs())


	"""
	We can clear diagnostic codes, but not like this:
	"""
	#elm.clearDTCs()

	"""
	Per ELM327 documentation, SAE standards specifies that the scantools must
	prevent users accidentally erasing DTCs, as it irreversibly erases potentially
	useful informmation. So the above line will raise an exception.

	Setting the first argument to 1 (or anything really) indicates "Yes I really mean
	to clear DTCs", it's up to the UI to implement a confirmation, then it can simply:
	"""
	#elm.clearDTCs(1)
