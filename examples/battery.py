#! /usr/bin/python

import time, sys
sys.path.append(".")
sys.path.append("..")
from elm327 import elm327, pids

with elm327.ELM327('/dev/ttyUSB0') as elm:
	print(elm.fetchBatteryLevel())
