import cellular, machine
import gps
import time
import urequests as requests
import ujson

running = False

def check(status):
    if status == 0 and running:
        machine.reset()
    if not running and status !=0:
        main()

def main():
    global running
    running = True
    # machine.watchdog_on(100)
    print('Ready')
    try:
        cellular.gprs('9mobile', '','')
    except:
        print('failed to initialize network')
        machine.reset()
    '''while True:
        lat, lon = gps.get_location()
        if lat != 90 and lon != 0:
            post_data = ujson.dumps({ 'lat': lat, 'lon': lon})
            request_url = 'https://bef4e1282cb799fd0f715580b5ac2c19.m.pipedream.net'
            requests.post(request_url, headers = {'content-type': 'application/json'}, data = post_data)
        for i in range(30):
            time.sleep(60)
            machine.watchdog_reset()'''

def handle_call(number):
    print(number)
    lat, lon = gps.get_location()
    if lat != 90 and lon != 0:
        cellular.SMS(number, 'Position https://www.google.com/maps/search/?api=1&query={},{}, bat={}%'.format(lat, lon, machine.get_input_voltage()[1])).send()
    else:
        cellular.SMS(number, 'No GPS fix').send()



print('GPS device')
gps.on()
cellular.on_call(handle_call)
started = False
def start():
    cellular.on_status_event(lambda status: check(status))
    if cellular.get_network_status():
        main()