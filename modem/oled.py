import i2c
from machine import Pin
import machine
import ssd1306
import utime


class Oled():

    def __init__(self):
        i2c.init(2, 50000)
        utime.sleep(10)
        self.display = ssd1306.SSD1306_I2C(128, 64, i2c)


    def home(self):
        self.display.fill(0)
        self.display.text('Microscale',10,10, 1)
        self.display.text('Embedded',10,25, 1)

        voltage = str(machine.get_input_voltage()[1])
        self.display.text('bat:' + voltage +' %',10,40, 1)
        self.display.show()

    def showincoming(self, phonenumber):
        self.display.fill(0)
        self.display.text('incoming...',10,10, 1)
        #utime.sleep(1)
        self.display.text(str(phonenumber),10,25, 1)
        #utime.sleep(1)
        self.display.show()

    def show_calling(self, phonenumber):
        self.display.fill(0)
        self.display.text('calling...',10,10, 1)
        #utime.sleep(1)
        self.display.text(str(phonenumber),10,25, 1)
        #utime.sleep(1)
        self.display.show()

    def show(self, ent):
        self.display.fill(0)
        self.display.text(ent,10,10, 1)
        self.display.show()