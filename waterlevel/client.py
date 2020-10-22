import uasyncio
import inspect

class client():
    def __init__(self):
        self.reader = None
        self.writer = None
        self.received = None
        self.managed = True

    async def connect(self, serverHost='cloud1.nodewire.org', failed=None):
        while True:
            try:
                print('connecting to {} ...'.format(serverHost))
                self.reader, self.writer = await uasyncio.open_connection(serverHost, 10001)
                while True:
                    try:
                        data = await self.reader.readline()
                        if len(data)==0 and self.received:
                            uasyncio.create_task(self.received('disconnected'))
                            break
                        if self.received:
                            try:
                                uasyncio.create_task(self.received(data.decode().strip()))
                            except Exception as ex1:
                                print(str(ex1))
                                if not self.managed: raise
                    except Exception as ex: # todo use specified exception type
                        print(str(ex))
                        if self.received:
                            self.received('disconnected')
                        break
                print('Close the socket')
                while True:
                    pass
                if failed!=None:
                    failed()
                self.writer.close()
                self.writer = None
                await uasyncio.sleep(10)
                print('trying to reconnect...')
            except Exception as Ex: # todo get the relevant exceptions: TimeoutError
                print(Ex)
                print('failed to connect')
                if failed!=None:
                    failed()
                    break
                await uasyncio.sleep(30)
                print('trying to reconnect...')

    def close_connection(self):
        if self.writer is not None:
            self.writer.close()
            self.writer = None

    async def sendasync(self, message):
        while(self.writer==None): await uasyncio.sleep(1)
        await self.writer.awrite(message.encode())

    async def send(self, message):
        await self.writer.awrite(message.encode())

if __name__ == '__main__':
    c = client()
    loop = uasyncio.get_event_loop()
    try:
        loop.run_until_complete(c.connect())
    except KeyboardInterrupt:
        pass
    loop.close()