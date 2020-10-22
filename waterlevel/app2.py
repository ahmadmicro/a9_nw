from hcsr04 import HCSR04
import cellular, machine
from control import control
import time
import uasyncio

running = False
sensor = HCSR04(trigger_pin=16, echo_pin=18)

class Handler():
    def __init__(self):
        self.auto = False
        self.times = 0
        self.height = 0

    def get_count(self, Sender):
        return self.times

    def on_start(self, Sender, Value):
        cellular.SMS(Value['phone'], '{}\nLevel is {} Ltrs'.format(Value["name"], Value["volume"])).send()

    async def loop(self):
        while True:
            await uasyncio.sleep(5)
            try:
                d = sensor.distance()
                # print(d)
                distance =  3321 - int(3.14159 *(152/2)*(152/2)*d/1000)
                #distance = 5612 - int(3.14159 *(183/2)*(183/2)*d/1000) # tank 2
                #distance = 2891 - int(3.14159 *(143/2)*(143/2)*d/1000) # tank 3 or 4

                #distance = 5311 - int(3.14159 *(170/2)*(170/2)*d/1000)
                # distance = 5612 - int(3.14159 *(183/2)*(183/2)*d/1000) # tank 2
                #distance = 2891 - int(3.14159 *(143/2)*(143/2)*d/1000) # tank 3
            except Exception as ex:
                print(ex)
                continue
            machine.watchdog_reset()
            if time.time() - ctrl.nw.last_received > 60 * 20:
                print('time out')
                machine.reset()
                while True:
                    pass
            if abs(self.height-distance)>1:
                ctrl.height = self.height = distance
            if ctrl.start == 1 or self.auto == 1:
                self.times+=1
                ctrl.count = self.times

def main():
    global ctrl, running
    running = True
    machine.watchdog_on(30)
    print('Ready')
    try:
        cellular.gprs('9mobile', '','')
    except:
        print('failed to initialize network')
        machine.reset()
        while True:
            pass

    handler = Handler()
    ctrl = control('waterlevel', inputs='start', outputs='height', handler=handler)
    ctrl.nw.debug = True
    ctrl.nw.run(handler.loop())

def check(status):
    if status == 0 and running:
        machine.reset()
        while True:
            pass
    if not running and status !=0:
        main()

def handle_call(number):
    print(number)
    machine.watchdog_on(30)
    if number == '08183387363':
        machine.reset()
        while True:
            pass

print('Water Level Monitor')
cellular.on_status_event(lambda status: check(status))
cellular.on_call(handle_call)
if cellular.get_network_status():
    main()
