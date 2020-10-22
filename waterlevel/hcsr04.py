# HC-SR04 Ultrasound Sensor
import time
from machine import Pin

# WeMos D4 maps GPIO2 machine.Pin(2) = TRIGGER
# WeMos D2 maps GPIO4 machine.Pin(4) = ECHO
triggerPort = 16
echoPort = 18
class HCSR04:
    def __init__(self, trigger_pin, echo_pin):
        self.trigger = Pin(trigger_pin, Pin.OUT)
        self.echo = Pin(echo_pin, Pin.IN)
        self.trigger.value(0)
        self.oldval = 0
        self.lastgood = 0

    def distance(self):
        # short impulse 10 microsec to trigger
        self.trigger.value(1)
        time.sleep_us(10)
        self.trigger.value(0)
        count = 0
        # Now loop until echo goes high
        start = time.ticks_us() 
        while not self.echo.value():
            if time.ticks_us() - start>38000: raise Exception("Sensor not responding")
        start = time.ticks_us() # get time in usec
        while self.echo.value():
            time.sleep_us(10)
            count += 1
            if count > 100:
                raise Exception("Counter exceeded")
        # duration = time.ticks_us() - start # time.ticks_diff(start, time.ticks_us()) # compute time difference
        duration = time.ticks_diff(time.ticks_us(), start)
        # After 38ms is out of range of the sensor
        if duration > 38000 :
            raise Exception("Out of range")

        # distance is speed of sound [340.29 m/s = 0.034029 cm/us] per half duration
        d = 0.017015 * duration
        if abs(d-self.oldval)>1:
            self.oldval = d
            return self.lastgood
        self.oldval = d
        self.lastgood = d
        return d