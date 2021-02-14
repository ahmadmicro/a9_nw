import cellular, machine
from control import control
import sys

running = False
led = machine.Pin(4, machine.Pin.OUT, 0)

class Handler():
    def on_led(self, Sender, Value):
        led.value(Value)


def main():
    global ctrl, running
    running = True
    print('Ready')
    try:
        cellular.gprs('9mobile', '','')
    except:
        print('failed to initialize network')
        sys.exit()

    handler = Handler()
    ctrl = control('blinky', inputs='led', handler=handler)
    ctrl.nw.debug = True
    ctrl.nw.run()

def check(status):
    if not running and status !=0:
        main()


print('Blinky')
cellular.on_status_event(lambda status: check(status))
if cellular.get_network_status():
    main()
