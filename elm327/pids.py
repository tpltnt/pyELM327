"""
Python module presenting an API to an ELM327 serial interface
(C) 2015 Jamie Fraser <fwaggle@fwaggle.org>
http://github.com/fwaggle/pyELM327

Python 3 port (C) 2017 by tpltnt <tpltnt.github@dropcut.net>
https://github.com/tpltnt/pyELM327

Please see License.txt and Readme.md.
"""

# Pretty much taken from https://en.wikipedia.org/wiki/OBD-II_PIDs
__pids = {
                0x01: {
                        # TODO: ignoring fuel system #2 atm
                        0x03: {
                                'Name': 'Fuel system status',
                                'Units': '',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) [A-Z0-9]{2} $',
                                'Value': lambda m: decode_0x03(int(m.group(1), 16))},
                        0x04: {
                                'Name': 'Calculated engine load value',
                                'Units': '%',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: int(m.group(1), 16) * 100.0 / 255},
                        0x05: {
                                'Name': 'Engine coolant temperature',
                                'Units': '*C',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: int(m.group(1), 16) - 40},
                        0x06: {
                                'Name': 'Short term fuel % trim - Bank 1',
                                'Units': '%',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: (int(m.group(1), 16)-128) * 100.0 / 128},
                        0x07: {
                                'Name': 'Long term fuel % trim - Bank 1',
                                'Units': '%',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: (int(m.group(1), 16)-128) * 100.0 / 128},
                        0x08: {
                                'Name': 'Short term fuel % trim - Bank 2',
                                'Units': '%',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: (int(m.group(1), 16)-128) * 100.0 / 128},
                        0x09: {
                                'Name': 'Long term fuel % trim - Bank 2',
                                'Units': '%',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: (int(m.group(1), 16)-128) * 100.0 / 128},
                        0x0A: {
                                'Name': 'Fuel pressure',
                                'Units': 'kPa (gauge)',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: int(m.group(1), 16) * 3},
                        0x0B: {
                                'Name': 'Intake manifold absolute pressure',
                                'Units': 'kPa (absolute)',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: int(m.group(1), 16)},
                        0x0C: {
                                'Name': 'Engine RPM',
                                'Units': 'RPM',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) ([A-Z0-9]{2}) $',
                                'Value': lambda m: ((int(m.group(1), 16) * 256) + int(m.group(2), 16))/4.0},
                        0x0D: {
                                'Name': 'Vehicle speed',
                                'Units': 'km/h',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: int(m.group(1), 16)},
                        0x0E: {
                                'Name': 'Timing advance',
                                'Units': '* rel #1 cylinder',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: (int(m.group(1), 16) - 128) / 2.0},
                        0x0F: {
                                'Name': 'Intake air temperature',
                                'Units': '*C',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: int(m.group(1), 16) - 40},
                        0x10: {
                                'Name': 'MAF Sensor air flow rate',
                                'Units': 'grams/sec',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) ([A-Z0-9]{2}) $',
                                'Value': lambda m: ((int(m.group(1), 16) * 256) + int(m.group(2), 16))/100.0},
                        0x11: {
                                'Name': 'Throttle position',
                                'Units': '%',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: (int(m.group(1), 16) * 100.0) / 255},
                        0x12: {
                                'Name': 'Commanded secondary air status',
                                'Units': 'Bit-encoded',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: int(m.group(1), 16)},
                        0x13: {
                                'Name': 'Oxygen sensors present',
                                'Units': 'Bit-encoded',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: int(m.group(1), 16)},

                        # NOTE: We currently throw away the fuel trim readings
                        # for these PIDs
                        0x14: {
                                'Name': 'Bank 1, Sensor 1: Oxygen sensor voltage',
                                'Units': 'V',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) [A-Z0-9]{2} $',
                                'Value': lambda m: ((int(m.group(1), 16) / 200))},
                        0x15: {
                                'Name': 'Bank 1, Sensor 2: Oxygen sensor voltage',
                                'Units': 'V',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) [A-Z0-9]{2} $',
                                'Value': lambda m: ((int(m.group(1), 16) / 200))},
                        0x16: {
                                'Name': 'Bank 1, Sensor 3: Oxygen sensor voltage',
                                'Units': 'V',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) [A-Z0-9]{2} $',
                                'Value': lambda m: ((int(m.group(1), 16) / 200))},
                        0x17: {
                                'Name': 'Bank 1, Sensor 4 Oxygen sensor voltage',
                                'Units': 'V',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) [A-Z0-9]{2} $',
                                'Value': lambda m: ((int(m.group(1), 16) / 200))},
                        0x18: {
                                'Name': 'Bank 2, Sensor 1: Oxygen sensor voltage',
                                'Units': 'V',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) [A-Z0-9]{2} $',
                                'Value': lambda m: ((int(m.group(1), 16) / 200))},
                        0x19: {
                                'Name': 'Bank 2, Sensor 2: Oxygen sensor voltage',
                                'Units': 'V',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) [A-Z0-9]{2} $',
                                'Value': lambda m: ((int(m.group(1), 16) / 200))},
                        0x1A: {
                                'Name': 'Bank 2, Sensor 3: Oxygen sensor voltage',
                                'Units': 'V',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) [A-Z0-9]{2} $',
                                'Value': lambda m: ((int(m.group(1), 16) / 200))},
                        0x1B: {
                                'Name': 'Bank 2, Sensor 4 Oxygen sensor voltage',
                                'Units': 'V',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) [A-Z0-9]{2} $',
                                'Value': lambda m: ((int(m.group(1), 16) / 200))},

                        0x1C: {
                                'Name': 'OBD standards this vehicle conforms to',
                                'Units': '',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: decode_0x1c(int(m.group(1), 16))},
                        0x1F: {
                                'Name': 'Run time since engine start',
                                'Units': 's',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) ([A-Z0-9]{2}) $',
                                'Value': lambda m: (int(m.group(1), 16) * 256) + int(m.group(2), 16)},
                        0x21: {
                                'Name': 'Distance traveled with malfuction indicator lamp on',
                                'Units': 'km',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) ([A-Z0-9]{2}) $',
                                'Value': lambda m: (int(m.group(1), 16) * 256) + int(m.group(2), 16)},
                        0x22: {
                                'Name': 'Fuel Rail Pressure (relative to manifold vacuum)',
                                'Units': 'kPa',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) ([A-Z0-9]{2}) $',
                                'Value': lambda m: (int(m.group(1), 16) * 256) + int(m.group(2), 16) * 0.079},
                        0x23: {
                                'Name': 'Fuel Rail Pressure (diesel, or gasoline direct injection)',
                                'Units': 'kPa',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) ([A-Z0-9]{2}) $',
                                'Value': lambda m: (int(m.group(1), 16) * 256) + int(m.group(2), 16) * 10},
                        0x2C: {
                                'Name': 'Commanded EGR',
                                'Units': '%',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: (int(m.group(1), 16) * 100.0) / 255},
                        0x2D: {
                                'Name': 'EGR Error',
                                'Units': '%',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: ((int(m.group(1), 16) - 128) * 100.0) / 128},
                        0x2E: {
                                'Name': 'Commanded evaporative purge',
                                'Units': '%',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: (int(m.group(1), 16) * 100.0) / 255},
                        0x2F: {
                                'Name': 'Fuel level input',
                                'Units': '%',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: (int(m.group(1), 16) * 100.0) / 255},
                        0x30: {
                                'Name': '# of warm-ups since codes cleared',
                                'Units': '%',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: int(m.group(1), 16)},
                        0x31: {
                                'Name': 'Distance traveled since codes cleared',
                                'Units': 'km',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) ([A-Z0-9]{2}) $',
                                'Value': lambda m: (int(m.group(1), 16) * 256) + int(m.group(2), 16)},
                        0x33: {
                                'Name': 'Barometric pressure',
                                'Units': 'kPa (absolute)',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: int(m.group(1), 16)},
                        0x42: {
                                'Name': 'Control module voltage',
                                'Units': 'V',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) ([A-Z0-9]{2}) $',
                                'Value': lambda m: (int(m.group(1), 16) * 256) + int(m.group(2), 16) / 1000.0},
                        0x43: {
                                'Name': 'Absolute load value',
                                'Units': '%',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) ([A-Z0-9]{2}) $',
                                'Value': lambda m: (int(m.group(1), 16) * 256) + int(m.group(2), 16) * 100.0 / 255},
                        0x44: {
                                'Name': 'Fuel/Air commanded equivalence ratio',
                                'Units': '',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) ([A-Z0-9]{2}) $',
                                'Value': lambda m: (int(m.group(1), 16) * 256) + int(m.group(2), 16) / 32768.0},
                        0x45: {
                                'Name': 'Relative throttle position',
                                'Units': '%',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: int(m.group(1), 16) * 100.0 / 255},
                        0x46: {
                                'Name': 'Ambient air temperature',
                                'Units': '*C',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: int(m.group(1), 16) - 40},
                        0x47: {
                                'Name': 'Absolute throttle position B',
                                'Units': '%',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: int(m.group(1), 16) * 100.0 / 255},
                        0x48: {
                                'Name': 'Absolute throttle position C',
                                'Units': '%',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: int(m.group(1), 16) * 100.0 / 255},
                        0x49: {
                                'Name': 'Absolute throttle position D',
                                'Units': '%',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: int(m.group(1), 16) * 100.0 / 255},
                        0x4A: {
                                'Name': 'Absolute throttle position E',
                                'Units': '%',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: int(m.group(1), 16) * 100.0 / 255},
                        0x4B: {
                                'Name': 'Absolute throttle position F',
                                'Units': '%',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: int(m.group(1), 16) * 100.0 / 255},
                        0x4C: {
                                'Name': 'Commanded throttle actuator',
                                'Units': '%',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: int(m.group(1), 16) * 100.0 / 255},
                        0x4D: {
                                'Name': 'Time run with MIL on',
                                'Units': 'minutes',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) ([A-Z0-9]{2}) $',
                                'Value': lambda m: (int(m.group(1), 16) * 256) + int(m.group(2), 16)},
                        0x4E: {
                                'Name': 'Time since codes cleared',
                                'Units': 'minutes',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) ([A-Z0-9]{2}) $',
                                'Value': lambda m: (int(m.group(1), 16) * 256) + int(m.group(2), 16)},
                        0x52: {
                                'Name': 'Fuel ethanol percentage',
                                'Units': '%',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: int(m.group(1), 16) * 100.0 / 255},
                        0x53: {
                                'Name': 'Absolute evaporative system vapor pressure',
                                'Units': 'kPa',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) ([A-Z0-9]{2}) $',
                                'Value': lambda m: ((int(m.group(1), 16) * 256) + int(m.group(2), 16)) / 200.0},
                        0x54: {
                                'Name': 'Relative evaporative system vapor pressure',
                                'Units': 'kPa',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) ([A-Z0-9]{2}) $',
                                'Value': lambda m: ((int(m.group(1), 16) * 256) + int(m.group(2), 16)) - 32767},
                        0x59: {
                                'Name': 'Absolute fuel rail pressure',
                                'Units': 'kPa',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) ([A-Z0-9]{2}) $',
                                'Value': lambda m: ((int(m.group(1), 16) * 256) + int(m.group(2), 16)) * 10},
                        0x5A: {
                                'Name': 'Relative accelerator pedal position',
                                'Units': '%',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: int(m.group(1), 16) * 100.0 / 255},
                        0x5B: {
                                'Name': 'Hybrid battery pack remaining life',
                                'Units': '%',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: int(m.group(1), 16) * 100.0 / 255},
                        0x5C: {
                                'Name': 'Engine oil temperature	',
                                'Units': '*C',
                                'Pattern': '^[A-Z0-9]{2} [A-Z0-9]{2} ([A-Z0-9]{2}) $',
                                'Value': lambda m: int(m.group(1), 16) - 40},
                }
        }

# Most of these strings also stolen mercilessly from Wikipedia


def decode_0x03(data):
    """
    Decode the bit-encoding of Mode 01, PID 03 and return appropriate string.

    This is apparently bit-encoded, but only one bit may be set at any one time.
    If you want the raw value, just do int([0:1]) on the string.
    """
    if data == 1:
        return '01: Open loop due to insufficient engine temperature'
    elif data == 2:
        return '02: Closed loop, using oxygen sensor feedback to determine fuel mix'
    elif data == 4:
        return '04: Open loop due to engine load OR fuel cut due to deceleration'
    elif data == 8:
        return '08: Open loop due to system failure'
    elif data == 16:
        return '16: Closed loop, using at least one oxygen sensor but there is a fault in the feedback system'
    else:
        return 'NO DATA'


__standards = {
        1:	'OBD-II as defined by the CARB',
        2:	'OBD as defined by the EPA',
        3:	'OBD and OBD-II',
        4:	'OBD-I',
        5:	'Not OBD compliant',
        6:	'EOBD (Europe)',
        7:	'EOBD and OBD-II',
        8:	'EOBD and OBD',
        9:	'EOBD, OBD and OBD II',
        10:	'JOBD (Japan)',
        11:	'JOBD and OBD II',
        12:	'JOBD and EOBD',
        13:	'JOBD, EOBD, and OBD II',
        14:	'Reserved',
        15:	'Reserved',
        16:	'Reserved',
        17:	'Engine Manufacturer Diagnostics (EMD)',
        18:	'Engine Manufacturer Diagnostics Enhanced (EMD+)',
        19:	'Heavy Duty On-Board Diagnostics (Child/Partial) (HD OBD-C)',
        20:	'Heavy Duty On-Board Diagnostics (HD OBD)',
        21:	'World Wide Harmonized OBD (WWH OBD)',
        22:	'Reserved',
        23:	'Heavy Duty Euro OBD Stage I without NOx control (HD EOBD-I)',
        24:	'Heavy Duty Euro OBD Stage I with NOx control (HD EOBD-I N)',
        25:	'Heavy Duty Euro OBD Stage II without NOx control (HD EOBD-II)',
        26:	'Heavy Duty Euro OBD Stage II with NOx control (HD EOBD-II N)',
        27:	'Reserved',
        28:	'Brazil OBD Phase 1 (OBDBr-1)',
        29:	'Brazil OBD Phase 2 (OBDBr-2)',
        30:	'Korean OBD (KOBD)',
        31:	'India OBD I (IOBD I)',
        32:	'India OBD II (IOBD II)',
        33:	'Heavy Duty Euro OBD Stage VI (HD EOBD-IV)',
}


def decode_0x1c(data):
    """
    Decode the bit-encoding of Mode 01, PID 1C.

    Returns a string describing the standards adhered to by the ECU.
    If you want the raw value, use int([0:2]) on the result.
    """
    if data in __standards:
        return '%3d: %s' % (data, __standards[data])
    else:
        return 'NO DATA'
