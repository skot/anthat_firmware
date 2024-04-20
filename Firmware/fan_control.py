import smbus
import sys


# Setup I2C port for EMC2305
EMC2305_ADDR = 0x4D

PRODUCT_ID_REG = 0xFD

FAN_TACH_HI = [0x3E, 0x4E, 0x5E, 0x6E]
FAN_TACH_LO = [0x3F, 0x4F, 0x5F, 0x6F]

TACH_TARGET = [0x3D, 0x4D, 0x5D, 0x6D]
DRIVE_SETTING = [0x30, 0x40, 0x50, 0x60]

PWM_OUTPUT_CONFIG = 0x2B
OUTPUT_CONFIG_OD = 0x00
OUTPUT_CONFIG_PP = 0xFF

def prettyHex(data):
    print("[", end="")
    for i in data[:-1]:
        print("%02X " % i, end="")
    print("%02X]" % data[-1])

def getFanSpeed(device, fan):
    try:
        data = device.read_i2c_block_data(EMC2305_ADDR, FAN_TACH_HI[fan], 2)
        fan_counts = ((data[0] << 8) | data[1]) >> 3
        fan_speed = 983040 / fan_counts

        FAN_EDGES = 5
        FAN_POLES = 2
        EMC2305_TACH_FREQ = 32768
        EMC2305_RPM_CONST_VAL = 60
        RANGE = 4

        # tachval = ((((FAN_EDGES - 1) * EMC2305_TACH_FREQ * EMC2305_RPM_CONST_VAL) / FAN_POLES) * (FAN_POLES)) / fan_counts
        tachval = 3932160 * RANGE / fan_counts


        print("Fan %d speed: %d" % (fan, tachval))
    except:
        print("No response")
    return fan_speed

def setFanSpeedRPM(device, fan, speed):
    # speed is in percent
    target = int((speed * 8191)) << 3
    target_hi = target >> 8
    target_lo = target & 0xFF
    print("Setting fan %d speed to %02X %02X" % (fan, target_hi, target_lo))
    device.write_i2c_block_data(EMC2305_ADDR, TACH_TARGET[fan], [target_lo, target_hi])

def setFanSpeedPWM(device, fan, speed):
    # speed is in percent
    target = int(((speed / 100.0) * 255))
    print("Setting fan %d speed to %.2f" % (fan, speed))
    device.write_byte_data(EMC2305_ADDR, DRIVE_SETTING[fan], target)

# get the fan speed from the command line
fan_speed = float(sys.argv[1])

# Initialize I2C controller
i2c = smbus.SMBus(1)

try:
    data = i2c.read_byte_data(EMC2305_ADDR, PRODUCT_ID_REG)
    print("PRODUCT_ID_REG: 0x%02X" % data) # should be 0x34
except:
    print("No response")

# set fan drivers to push-pull
print("Setting PWM output config to open drain")
i2c.write_byte_data(EMC2305_ADDR, PWM_OUTPUT_CONFIG, OUTPUT_CONFIG_OD)

setFanSpeedPWM(i2c, 0, fan_speed)
setFanSpeedPWM(i2c, 1, fan_speed)
setFanSpeedPWM(i2c, 2, fan_speed)
setFanSpeedPWM(i2c, 3, fan_speed)

getFanSpeed(i2c, 0)
getFanSpeed(i2c, 1)
getFanSpeed(i2c, 2)
getFanSpeed(i2c, 3)