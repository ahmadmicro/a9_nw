from nodewire import NodeWire
import ujson
import inspect
import uasyncio


will_get = {}

class Node():
    def __init__(self, nw, name, gateway):
        self.name = name
        self.nw = nw
        self.gateway = gateway
        self.ports = {}

    def __iter__(self):
        self.iterobj = iter(self.ports)
        return self.iterobj

    def __next__(self):
        next(self.iterobj)

    def __unicode__(self):
        return self.name + str(self.ports)

    def __repr__(self):
        return self.name + str(self.ports)

    def __str__(self):
        return self.name + str(self.ports)

    def __contains__(self, item):
        return item in self.ports

    def __getitem__(self, item):
        if item in self.ports:
            return self.ports[item]
        elif item == 'name':
            return self.name
        else:
            return None

    def __setitem__(self, key, value):
        self.nw.send2(self.gateway+':'+self.name, 'set', key, ujson.dumps(value))

    def set(self, key,value):
        self.ports[key] = value

    def __getattr__(self, item):
        return self.__getitem__(item)

    def __setattr__(self, key, value):
        if key in ['nw', 'name', 'gateway', 'ports']:
            super(Node, self).__setattr__(key, value)
        else:
            if key.startswith('on_'):
                self.__dict__[key] = value
                #super(Node, self).__setattr__(key, value) # todo: check if this is a method
            else:
                self.__setitem__(key, value)

class control:
    def __init__(self, nodename='control', inputs='', outputs='', handler = None):
        self.nw = NodeWire(nodename, process=self.process)
        self.nw.debug = False
        self.nodes = []
        self.sender = None
        self.inputs =  [{'port':i.split(':')[0] if ':' in i else i, 'props': i.split(':')[1] if ':' in i else 'Status', 'value':0} for i in  inputs.split()]
        self.outputs = [{'port':o.split(':')[0] if ':' in o else o, 'props': o.split(':')[1] if ':' in o else 'Status'} for o in outputs.split()]

        if not handler is None:
            for method in inspect.getmembers(handler, inspect.ismethod):
                if method[0].startswith('get_'):
                    port = method[0][4:]
                    ports = [p for p in self.outputs if p['port'] == port]
                    if ports != []: ports[0]['get'] = method[1]
                elif method[0].startswith('on_'):
                    port = method[0][3:]
                    ports = [p for p in self.inputs if p['port'] == port]
                    if ports != []: ports[0]['on'] = method[1]
        
        # https://stackoverflow.com/questions/845110/emulating-pass-by-value-behaviour-in-python
        if len(self.inputs) >= 1:
            setattr(self.__class__, self.inputs[0]['port'], property(lambda self: self.get(self.inputs[0]['port']), lambda self, v: self.set(self.inputs[0]['port'], v)))
        if len(self.inputs) >= 2:
            setattr(self.__class__, self.inputs[1]['port'], property(lambda self: self.get(self.inputs[1]['port']), lambda self, v: self.set(self.inputs[1]['port'], v)))
        if len(self.inputs) >= 3:
            setattr(self.__class__, self.inputs[2]['port'], property(lambda self: self.get(self.inputs[2]['port']), lambda self, v: self.set(self.inputs[2]['port'], v)))
        if len(self.outputs) >= 1:
            setattr(self.__class__, self.outputs[0]['port'], property(lambda self: self.get(self.outputs[0]['port']), lambda self, v: self.set(self.outputs[0]['port'], v)))
        if len(self.outputs) >= 2:
            setattr(self.__class__, self.outputs[1]['port'], property(lambda self: self.get(self.outputs[1]['port']), lambda self, v: self.set(self.outputs[1]['port'], v)))
        if len(self.outputs) >= 3:
            setattr(self.__class__, self.outputs[2]['port'], property(lambda self: self.get(self.outputs[2]['port']), lambda self, v: self.set(self.outputs[2]['port'], v)))
        '''for port in self.outputs:
            setattr(self.__class__, port['port'], property(lambda self: self.get(port['port']), lambda self, v: self.set(port['port'], v)))
        for port2 in range(len(self.inputs)):
            setattr(self.__class__, self.inputs[port2]['port'], property(lambda self: self.get(self.inputs[port2]['port']), lambda self, v: self.set(self.inputs[port2]['port'], v)))'''
        

    def get(self, item):
        ports = [p for p in self.outputs if p['port'] == item]
        if ports != []:
            port = ports[0]
            if 'get' in port:
                return port['get'](Sender=self.sender)
            elif 'value' in port:
                return port['value']
            else:
                return 0
        else:
            ports = [p for p in self.inputs if p['port']==item]
            if ports != []:
                port = ports[0]
                return port['value']
            else:
                print('invalid port or attribute: {}'.format(item))
                return None
                # raise Exception('invalid port or attribute: {}'.format(item))

    def set(self, key, value):
        ports = [p for p in self.inputs if p['port'] == key]
        if ports != []:
            ports[0]['value'] = value
            if 'on' in ports[0]:
                ports[0]['on'](Sender=self.sender, Value=value)
        else:
            ports = [p for p in self.outputs if p['port'] == key]
            if ports != []:
                self.nw.send2('re', 'portvalue', key, ujson.dumps(value))

    '''def __getattr__(self, item):
        if item in ['nw', 'nodes', 'sender', 'inputs', 'outputs']:
            return super(control, self).__getattr__(item)
        ports = [p for p in self.inputs if p['port']==item]
        if ports != []:
            port = ports[0]
            return port['value']
        else:
            return self.get(item)'''

    def __setattr__(self, key, value):
        if key in ['nw', 'nodes', 'sender', 'inputs', 'outputs', 'queue']:
            super(control, self).__setattr__(key, value)
        else:
            if key.startswith('on_'):
                port = key[3:]
                ports = [p for p in self.inputs if p['port'] == port]
                if ports!=[]: ports[0]['on']=value
            elif key.startswith('get_'):
                port = key[4:]
                ports = [p for p in self.outputs if p['port'] == port]
                if ports != []: ports[0]['get'] = value
            else:
                self.set(key, value)

    def create_node(self, nodename, instance=None, got_it=None):
        if instance==None: instance = self.nw.gateway
        nodes = [n for n in self.nodes if n.name==nodename]
        if len(nodes) == 0:
            self.nw.send2('cp','subscribe', nodename if instance==None else instance +':'+nodename, 'portvalue')
            self.nw.send2('cp', 'getnode', nodename)
            if got_it!=None:
                will_get[nodename] = got_it
        else:
            if got_it!=None: got_it(nodes[0])

    async def process(self, msg):
        if msg.Command == 'get':
            if msg.Port == 'ports':
                ports = ' '.join([o['port'] for o in self.outputs]) + ' ' + ' '.join([i['port'] for i in self.inputs])
                await self.nw.send(msg.Sender, 'ports', ports)
            elif msg.Port == 'properties':
                ports = [p for p in self.inputs if p['port'] == msg.Params[1]]
                if ports != []:
                    await self.nw.send(msg.Sender, 'properties', msg.Params[1], ports[0]['props'])
                else:
                    ports = [p for p in self.outputs if p['port'] == msg.Params[1]]
                    if ports != []:
                        await self.nw.send(msg.Sender, 'properties', msg.Params[1], ports[0]['props'])
            else:
                self.sender = msg.Sender
                result = getattr(self, msg.Port, None)
                await self.nw.send(msg.Sender, 'portvalue', msg.Port, ujson.dumps(result))
                self.sender = None
        elif msg.Command == 'set':
            if msg.Port in [p ['port'] for p in self.inputs]:
                self.sender = msg.Sender
                self.__setattr__(msg.Port, msg.Value)
                self.sender = None
                await self.nw.send(msg.Sender, 'portvalue', msg.Port, ujson.dumps(getattr(self, msg.Port, None)))
        elif msg.Command == 'portvalue':
            if ':' in msg.Sender:
                sender = msg.Sender.split(':')
                msg.Sender = sender[1]
                instance = sender[0]
            else:
                instance = None
            senders = [s for s in self.nodes if s.name==msg.Sender]
            if senders!=[]:
                senders[0].set(msg.Port, msg.Value)
                if 'on_' + msg.Port in senders[0].__dict__:
                    senders[0].__dict__['on_' + msg.Port](msg.Sender)
        elif msg.Command == 'node':
            msg.Params[0] = msg.Params[0].replace("'", '"')
            msg.Params[0] = msg.Params[0].replace('None', 'null')
            msg.Params[0] = msg.Params[0].replace('True', 'true')
            msg.Params[0] = msg.Params[0].replace('False', 'false')
            nodevalue = ujson.loads(msg.Params[0])
            nodename = msg.Params[1]
            gateway = msg.Params[2]
            n = Node(self.nw, nodename, gateway)
            if n not in self.nodes:
                for key in nodevalue:
                    n.set(key, nodevalue[key])
                self.nodes.append(n)
            if nodename in will_get:
                will_get[nodename](n)
                del will_get[nodename]

class Handler():
    def __init__(self):
        self.auto = False
        self.times = 0

    def lost_power(self, node):
        if sco.mains == 0 and self.auto: sco.ignition = 1
        self.times+=1

    def on_auto_switched(self, sender, value):
        self.auto = value

    def get_service_required(self, Sender):
        return self.times>10

    def connected(self, node=None):
        global sco
        if node is None:
            ctrl.create_node('sco', got_it=self.connected)
        else:
            sco = node
            sco.on_mains = self.lost_power

if __name__ == '__main__':
    ## MAIN PROGRAM
    handler = Handler()
    ctrl = control(inputs = 'auto_switch', outputs = 'service_required', handler=handler)
    ctrl.nw.on_connected = handler.connected
    ctrl.nw.debug = True
    ctrl.nw.run()