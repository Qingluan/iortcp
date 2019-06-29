from base64 import b64encode, b64decode
from sys import version
from hshadow.common import to_bytes
if version[0] == '2':
    def En(data):
        return data
        #data = ''.join([bytes(ord(i)-1) for i in data])
        return b64encode(data.encode())

    def De(data):
        return data
        data = b64decode(data.encode())
        #data = ''.join([bytes(ord(i)+1) for i in data])
        return data.encode()
else:
    def En(data):
        data = bytes([i ^ 110 for i in data])
        #return b64encode(data)
        return data
    def De(data):
        data = bytes([i ^ 110 for i in data])
        #return b64decode(data)
        return data
