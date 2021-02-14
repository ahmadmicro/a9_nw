import cellular, machine
from control import control
import sys
import gps
import uasyncio

running = False

class Handler():
    def __init__(self):
        self.bat = 0

    def on_check(self, Sender, Value):
        ctrl.location = self.get_location(Sender)

    def get_location(self, Sender):
        lat, lon = gps.get_location()
        location = {
            'lat': lat,
            'lon': lon
        }
        return location

    def get_bat(self, Sender):
        return machine.get_input_voltage()[1]

    async def loop(self):
        while True:
            await uasyncio.sleep(5*60)
            ctrl.location = self.get_location(None)
            if self.bat != machine.get_input_voltage()[1]:
                self.bat = ctrl.bat = machine.get_input_voltage()[1]


def main():
    global ctrl, running
    running = True
    print('Ready')
    try:
        cellular.gprs('9mobile', '','')
    except:
        print('failed to initialize network')
        machine.reset()

    handler = Handler()
    ctrl = control('gps_####', inputs='check', outputs='location bat', handler=handler)
    ctrl.nw.debug = True
    ctrl.nw.run(handler.loop())

def check(status):
    if status == 0 and running:
        machine.reset()
    if not running and status !=0:
        main()

def handle_call(number):
    print(number)
    if number == '08183387363':
        machine.reset()


print('gps')
gps.on()
cellular.on_status_event(lambda status: check(status))
cellular.on_call(handle_call)
if cellular.get_network_status():
    main()
