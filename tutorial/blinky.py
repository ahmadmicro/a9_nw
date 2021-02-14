
import machine
import time

led = machine.Pin(4, machine.Pin.OUT, 0)
value = 1
for i in range(100):
    led.value(value)
    time.sleep(1)
    value = 0 if (value==1) else 1