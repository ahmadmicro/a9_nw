import cellular, machine
import keypad
from oled import Oled
import os
import sys

running = False

def main():
    global running
    running = True
    print('Ready')
    keypad.run(keypad_watcher)

def check(status):
    if status == 0:
        oled.show('no network')
    if status !=0:
        oled.home()
        if not running:
            main()

def handle_call(number):
    if number == True or number == False:
        oled.home()
    else:
        print('incoming: {}'.format(number))
        oled.showincoming(number)

entered = ''

async def keypad_watcher(keypad):
    global entered
    while True:
        key = await keypad.get_key()
        if key not in ['L', 'E', 'R', 'C', 'K']:
            entered = entered + key
            print('entry:', entered)
            oled.show(entered)
        elif key == 'K':
            print('OK')
            try:
                if entered == '4444':
                    os.remove('boot.py')
                    oled.show('Debug mode')
                    break
                '''elif entered.startswith('*'):
                    result = cellular.ussd(entered)
                    print(result)
                    oled.show(result)'''
                elif entered != '':
                    oled.show_calling(entered)
                    cellular.dial(entered)
                else:
                    cellular.answer()
            except:
                pass
            entered = ''
        elif key == 'C':
            print('cancel')
            entered = ''
            cellular.dial(False)
            oled.home()
    sys.exit()



print('GSM Phone')
cellular.on_call(handle_call)
started = False
oled = Oled()
if not cellular.is_sim_present():
    oled.show('No SIM card')
cellular.on_status_event(lambda status: check(status))
if cellular.get_network_status():
    oled.home()
    main()
