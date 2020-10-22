from nodewire.control import control
import hashlib
import asyncio
import sys

def file_response(error):
    print(error)
    quit()

def connected(node=None):
    nodename = sys.argv[1]
    filename = sys.argv[2]
    if node is None:
        print(f'getting node {nodename}')
        ctrl.create_node(nodename, got_it=connected)
    else:
        print(f'sending file {filename}')
        file = open(filename, 'r')
        content = file.read()
        file.close()
        m = hashlib.md5()
        m.update(content.encode('utf-8'))
        node.on_file = file_response
        node.file = {
            'name': filename.split('\\')[-1],
            'content': content,
            'md5': 'str(m.digest())'
        }

async def compute():
    await asyncio.sleep(10)
    connected()

if __name__ == '__main__':
    ctrl = control()
    # ctrl.nw.debug = True
    ctrl.nw.run(compute())