import i2c
from machine import Pin
import machine
import ssd1306
import utime

i2c.init(2, 100000)
display = ssd1306.SSD1306_I2C(128, 64, i2c)
while True:
    display.text('Microscale',10,10, 1)
    display.text('Embedded',10,25, 1)
    display.show()

    voltage = str(machine.get_input_voltage()[1])
    display.text(voltage +' %',10,40, 0)
    display.text(voltage +' %',10,40, 1)
    display.show()
    utime.sleep(10)