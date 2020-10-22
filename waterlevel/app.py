from hcsr04 import HCSR04
import cellular, machine
from control import NodeWire
import time

print('Water Level Monitor')
time.sleep(3)
try:
    cellular.gprs('9mobile', '','')
except:
    machine.reset()

sensor = HCSR04(trigger_pin=16, echo_pin=18)

def main():
    nw = NodeWire('pyNode')
    nw.debug = True
    nw.run()

try:
    distance = sensor.distance()
    print('Distance:', distance, 'cm')

    main()
except Exception as ex:
    print('ERROR getting distance:', ex)