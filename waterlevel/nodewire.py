import time
from splitter import split
import uasyncio
import ujson
from client import client
import random
import queue
import machine
import uhashlib
import sys

debug = False # False for deployment

class Message:
    def __init__(self, msg):
        words = split(msg)
        self.Address = words[0]
        self.Command = words[1] if len(words)>1 else words[0]
        self.Params = words[2:-1] if len(words)>2 else words[0]
        self.Port = words[2] if len(words)>=4 else None
        try:
            self.Value = ujson.loads(words[3]) if len(words)>=5 else None
        except Exception as ex:
            print('msg value error: {}'.format(ex))
            self.Value = None
        self.Sender = words[-1]

    def __str__(self):
        return self.Address + ' ' + self.Command + ' ' + ' '.join(p for p  in self.Params) + ' ' + self.Sender

def uuid():
    random.seed(time.time())
    choice = ['0', '1','2','3','4','5','6','7','8','9','A','B','C','D','E','F']
    pattern = 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
    return ''.join([random.choice(choice) if c == 'x' else '-' for c in pattern])

class NodeWire:
    def __init__(self, node_name='node', server='cloud1.nodewire.org', process=None):
        self.name = node_name
        self.type = node_name
        self.server_address = server
        self.gateway = ''
        self.id = 'None'
        self.callbacks = {}
        self.terminated = False
        self.client = client()
        self.called_connected =  False
        self.connected = False
        self.last_received = time.time()

        self.ack = False
        self.waiting_config = False

        self.msgqueue = queue.Queue(10)

        try:
            self.readconfig()
            print(self.uuid)
        except:
            print('Failed to read configuration file. Creating new config...')
            self.uuid = str(uuid())
            print('New UUID is {}'.format(self.uuid))
            self.token = 'None'
            self.name = node_name
            self.id = 'None'
            self.saveconfig()

        if self.process_command:
            self.client.received = self.process_command

        self.process = process
        self.on_connected = None
        self.debug = False

    def saveconfig(self):
        file = open('nw.cfg', 'w')
        file.write(ujson.dumps({
            'uuid': self.uuid,
            'token': self.token,
            'name': self.name,
            'id': self.id,
            'gateway': self.gateway
        }))
        file.close()

    def readconfig(self):
        file = open('nw.cfg', 'r')
        config = ujson.loads(file.read())
        self.uuid = config['uuid']
        self.token = config['token']
        self.name = config['name']
        self.id = config['id']
        self.gateway = config['gateway']
        file.close()

    async def start(self, loop):
        print('started')
        if self.token == 'None':
            await self.client.sendasync('cp Gateway id={}\n'.format(self.uuid))
            self.waiting_config = True
        else:
            await self.client.sendasync('cp Gateway key={} {}\n'.format(self.token, self.uuid))
        self.connected = True
    
    def lostconnection(self):
        self.connected = False

    async def sender(self):
        while True:
            msg = await self.msgqueue.get()
            while not self.connected:
                await uasyncio.sleep(1)
            await self.client.send(msg)

    def send2(self, Node, Command, *Params):
        if self.connected:
            cmd = Node + ' ' + Command + ' ' + ' '.join(param for param in Params) + (' ' + self.name if len(Params) != 0 else self.name)
            if self.debug:print(cmd)
            self.msgqueue.put_nowait(cmd+'\n')
            return True

    async def send(self, Node, Command, *Params):
        if self.connected:
            try:
                #todo rewrite this as format function
                cmd = Node + ' ' + Command + ' ' + ' '.join(param for param in Params) + (' ' + self.name if len(Params) != 0 else self.name)
                if self.debug:print(cmd)
                await self.client.send(cmd+'\n')
                return True
            except Exception as ex:
                if self.debug:print('failed to send command over LAN')
                self.connected = False
                return False

    async def pinger(self):
        if self.debug: print('announcing...')
        while not self.ack:
            await self.send('cp', 'ThisIs', self.id)
            await uasyncio.sleep(5)

    async def keepalive(self):
        await uasyncio.sleep(60)
        while True:
            self.ack = False
            try:
                await self.send('cp', 'keepalive')
            except:
                await self.start(uasyncio.get_event_loop())
            await uasyncio.sleep(5)
            if not self.ack:
                if self.debug: print('didn\'t recieve ack')
                machine.watchdog_on(30)
                machine.reset()
                while True:
                    pass
            await uasyncio.sleep(300)

    def when(self, cmd, func):
        self.callbacks[cmd] = func

    async def process_command(self, cmd):
        self.last = time.time()
        if cmd == 'disconnected':
            self.connected = False
            return

        if self.debug: print(cmd)
        if cmd == '': 
            print('not received')
            return
        msg = Message(cmd)
        self.last_received = time.time()

        if msg.Command == 'ack':
            self.ack = True
        elif msg.Command == 'gack' and not self.called_connected:
            print('connected')
            if self.waiting_config:
                self.waiting_config = False
                self.gateway = msg.Address.split(':')[0]
                self.token = msg.Address.split(':')[1]
                self.saveconfig()
                self.client.close_connection()
                self.connected = False
                await self.start(uasyncio.get_event_loop())
            if self.on_connected:
                self.called_connected = True
                self.on_connected()
        elif msg.Command == 'authfail':
            if self.token != 'None':
                if self.debug: print('we have been deleted')
                self.token = 'None'
                self.saveconfig()
        elif msg.Command == 'ping':
            self.ack = False
            await self.send('cp', 'ThisIs', self.id)
            uasyncio.Task(self.pinger())
        elif msg.Command == 'get' and msg.Params[0] == 'id':
            await self.send(msg.Sender, 'id', self.id)
        elif msg.Command == 'get' and msg.Params[0] == 'type':
            await self.send(msg.Sender, 'type', self.type)
        elif msg.Command == 'set' and msg.Params[0] == 'id':
            self.id = msg.Params[1]
            self.saveconfig()
        elif msg.Command == 'set' and msg.Params[0] == 'name':
            self.name = msg.Params[1]
            self.saveconfig()
            await self.send(msg.Sender, 'ThisIs')
        elif msg.Command == 'set' and msg.Params[0] == 'exit':
            machine.watchdog_off()
            sys.exit()
        elif msg.Command == 'set' and msg.Params[0] == 'file':
            print(msg.Value)
            m = uhashlib.md5()
            m.update(msg.Value["content"].encode('utf-8'))
            #if msg.Value["md5"] == str(m.digest()):
            print('saved')
            file = open(msg.Value["name"], 'w')
            file.write(msg.Value["content"])
            file.close()
            await self.send(msg.Sender, 'portvalue', 'file', "'ok'")
            #else:
            #    await self.send(msg.Sender, 'portvalue', 'file', "'error'")
        else:
            if self.process:
                await self.process(msg)
        if msg.Command == 'portvalue':
            signal = (msg.Sender.split(':')[1] if ':' in msg.Sender else msg.Sender) + '.' + msg.Params[0]
            if signal in self.callbacks:
                self.callbacks[signal](msg)
        elif msg.Command in self.callbacks:
                self.callbacks[msg.Command](msg)

    async def run_async(self, tsk=None):
        loop = uasyncio.get_event_loop()
        if tsk:
            await uasyncio.gather(
                uasyncio.create_task(self.client.connect(serverHost=self.server_address, failed = self.lostconnection)),
                uasyncio.create_task(self.start(loop)),
                uasyncio.create_task(self.keepalive()),
                uasyncio.create_task(self.sender()),
                uasyncio.create_task(tsk)
            )
        else:
            await uasyncio.gather(
                uasyncio.create_task(self.client.connect(serverHost=self.server_address, failed = self.lostconnection)),
                uasyncio.create_task(self.start(loop)),
                uasyncio.create_task(self.keepalive()),
                uasyncio.create_task(self.sender())
            )

    async def run2(self, loop):
        uasyncio.Task(self.client.connect(serverHost=self.server_address, failed = self.lostconnection))
        uasyncio.Task(self.start(loop))
        uasyncio.Task(self.keepalive())
        uasyncio.create_task(self.sender())
        await uasyncio.sleep_ms(10_000)

    def run(self, tsk=None):
        loop = uasyncio.get_event_loop()
        loop.run_until_complete(self.run_async(tsk))

if __name__ == '__main__':
    nw = NodeWire('pyNode')
    nw.debug = True
    nw.run()