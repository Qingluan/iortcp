#!/bin/python
# from argparse import ArgumentParser
import socket
from socket import SO_REUSEADDR, SO_REUSEPORT, SOL_SOCKET
from socket import AF_INET, SOCK_STREAM
import sys 
import select
import time
# import pdb
if sys.version[0] == '2':
    class ConnectionResetError(Exception):pass
    class ConnectionRefusedError(Exception):pass

REVERSE_OP = b'[{_m0re_c0n_}]'

def _extract(r, k):
    l = len(k)
    f = r.find(k)
    rb = r[:f]
    rl = r[f+l:]
    return rb + rl

def create_server(port):
    sock = socket.socket(AF_INET, SOCK_STREAM)
    sock.bind(('',port))
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
    sock.listen(15)
    while 1:
        s,_ = sock.accept()
        yield s

def log(i, end='\n'):
    sys.stdout.write(i+end)
    sys.stdout.flush()

class SenderHandler:
    all_sender = []
    def __init__(self, addr=None, laddr=None, sock=None, lsock=None, alive_check_sec=7, init_con=1):
        if sock or lsock:
            self.sock = sock
            self.lsock = lsock
        else:
            # print(addr)
            self.sock = self.create_sock(addr)
            self.lsock = None
        self.laddr = laddr
        self.addr = addr
        self.to_ldata = b''
        self.to_rdata = b''
        self.unconnect = ''
        self.reset = False
        self._alive_interval = alive_check_sec
        self._time = time.time()
        self._now_handle_socks = {}

        self.regist_sock(self.sock)
        if self.lsock:
            self.regist_sock(self.lsock)
        
        self.regist_sender()

    def regist_sender(self):
        if self not in self.__class__.all_sender:
            self.__class__.all_sender.append(self)

    def unregist_sender(self):
        if self in self.__class__.all_sender:
            self.__class__.all_sender.remove(self)        

    def regist_sock(self, sock):
        if sock:
            self._now_handle_socks[sock.fileno()] = sock
            # self.regist_sender()

    def unregist_sock(self, sock):
        fn = sock.fileno()
        if fn != -1:
            del self._now_handle_socks[fn]
            # self.unregist_sender()
        

    def clean(self):
        ks = [k for k,v in self._now_handle_socks.items() if v.fileno() == -1]
        for k in ks:
            log('close: %d' % k)
            del self._now_handle_socks[k]

    def handle(self):
        # n = time.time()
        # if n - self._time > self._alive_interval:
            # self.check_alive(self.sock)
            # self._time = n
        if not self.lsock:
            self.unconnect = self.laddr
        if not self.sock:
            self.sock = self.create_sock(self.addr)
            self.regist_sock(self.sock)
        
        # pdb.set_trace()
        # all_socks.append(self.lsock)
        all_socks = self._now_handle_socks.values()
        for s in all_socks:
            if s.fileno() == -1:
                self.reset = True
                return
        rl,wl, _ = select.select( all_socks,all_socks, all_socks)
        for s in rl:
            self.handle_read(s)
        
        if self.to_ldata or self.to_rdata:
            for s in wl:
                self.handle_write(s)

        self.clean
        # log("reset : %s" % self.reset,end='\r')

    def handle_error(self, sock):
        sock.close()
        if sock != self.lsock and self.lsock:
            self.lsock.close()
            self.unregist_sock(self.lsock)
        self.reset = True
        self.unregist_sender()

    def handle_build_more(self, d):
        d = _extract(d, REVERSE_OP)
        ## connection more conn
        
        SenderHandler(addr=self.addr, laddr=self.laddr)
        SenderHandler(addr=self.addr, laddr=self.laddr)
        log("reverse connection: %d"% len(self.__class__.all_sender))
        return d

    def handle_read(self, sock):
        try:
            d = sock.recv(9216)
        except OSError:
            log("conn , break", end='\r')
            self.handle_error(sock)
            return
        if not d:
            log(".     no data , break", end='\r')
            self.handle_error(sock)
            return
        if sock == self.sock:
            log("from : %s | %d" %(self.addr, len(d)))
            if REVERSE_OP in d:
                d = self.handle_build_more(d)
                if not d:
                    return
            self.to_ldata += d
            if not self.lsock:
                self.lsock = self.create_sock(self.laddr)
                self.regist_sock(self.lsock)
        
        elif sock == self.lsock:
            log("from : %s" %self.laddr)
            self.to_rdata += d

    
        

    def handle_write(self, sock):
        dirty = False
        try:
            if sock == self.sock:
                sn = sock.send(self.to_rdata)
                # print(self.to_rdata)
                log("reverse <- %d " % sn, end='\r')

                self.to_rdata = self.to_rdata[sn:]
                if self.to_rdata:
                    dirty = True
            elif sock == self.lsock:
                sn = sock.send(self.to_ldata)
                # print(self.to_ldata)
                log("reverse -> %d  " % sn, end='\r')
                self.to_ldata = self.to_ldata[sn:]
                if self.to_ldata:
                    dirty = True
            
        except BrokenPipeError:
            log("socks break ! . reset")
            self.handle_error(sock)
            dirty = False

        if dirty:
            self.handle_write(sock)

    def check_alive(self, sock):
        r,w, _ = select.select([sock], [], [], 1)
        if len(r) > 0:
            d = r[0].recv(9216)
            if not d:
                return False
            if sock == self.sock:
                self.to_ldata += d
            else:
                self.to_rdata += d

    def create_sock(self, addr, block=False):
        if isinstance(addr, str):
            if ':' in addr:
                ip,port = addr.split(":")
                port = int(port)
            else:
                ip = 'localhost'
                port = int(addr)
        elif isinstance(addr, int):
            ip = 'localhost'
            port = addr
        else:
            ip = addr[0]
            port = addr[1]
        
        sock = socket.socket(AF_INET, SOCK_STREAM)
        sock.connect((ip, port))
        # log('%s:%d --> ok' % (ip,port), end='\r')
        sock.setblocking(block)
        return sock

    def handle_receive(self):
        n = self.sock.recv(9046)

class WaiterHandler(SenderHandler):

    def __init__(self, port_w, port_r):
        self.sock_w = self.create_server(port_w)
        self.sock_r = self.create_server(port_r)
        self.to_ldata = b''
        self.to_rdata = b''
        self.reset = False
        self.sock1 = None
        self.sock2 = None
        self.port_r = port_r
        self.port_w = port_w
        self._now_handle_socks = {}

        self.regist_sock(self.sock_r)
        self.regist_sock(self.sock_w)
        self._runing_handlers = []
        self.recv_list = []
        self.listen_list = []

    def handle(self):
        all_socks = self._now_handle_socks.values()
        # log(".")
        rl,_, _ = select.select( all_socks,[], [], 0.02)
        # log("..")
        
        paris = {}
        for i,s in enumerate(rl):
            sock,_ = s.accept()
            if s == self.sock_r:
                self.recv_list.append(sock)
            elif s == self.sock_w:
                self.listen_list.append(sock)

        # log("..")
        self.handle_check_alive()
        recv_list = self.recv_list
        listen_list = self.listen_list
        rcv_num = len(recv_list)
        lit_num = len(listen_list)
        log("listen: %d / revesr: %d "%(lit_num, rcv_num),end='\r')
        need_conn_num = 0
        if  rcv_num>0  or  lit_num>0:
            need_conn_num =  lit_num - rcv_num
            for i,rsock in enumerate(recv_list):
                if i < lit_num:
                    lsock = listen_list[i]
                    hand = SenderHandler(sock=lsock, lsock=rsock)
                    self.listen_list.remove(lsock)
                    self.recv_list.remove(rsock)
                    # hand.handle()
                    # log("conn build")
                    self._runing_handlers.append(hand)
            
        un_r = []
        for hand in self._runing_handlers:
            try:
                
                # bc += 1
                hand.handle()
                if hand.reset:
                    raise ConnectionResetError("break")
            except ConnectionResetError:
                log("connection break %r" % hand)
                un_r.append(hand)
        
        # clear break connection
        for u in un_r:
            self._runing_handlers.remove(u)

        if need_conn_num > 0 and len(self._runing_handlers) > 0:
            log("send cmd to create more conec")
            h = self._runing_handlers[0]
            h.to_ldata += REVERSE_OP
            h.handle_write(h.lsock)
                
    def handle_check_alive(self):
        al_s = self.recv_list
        rl, _ ,_ = select.select(al_s, [], [], 0.001)
        for s in rl:
            d = s.recv(1024)
            if not d:
                self.recv_list.remove(s)
            else:
                log("error: %s"% d)




    def init(self):
        log("init")
        
        self.sock1.close()
        self.sock1 = None


        self.sock2.close()
        self.sock2 = None

    def create_server(self, port):
        sock = socket.socket(AF_INET, SOCK_STREAM)
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        # sock.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)

        sock.bind(('',port))
        
        sock.setblocking(False)
        sock.listen(1024)
        return sock


def ConnectServer(lport, rport):
    ic = 0
    
    R = WaiterHandler(lport, rport)
    while 1:        
        ic +=1
        R.handle()
        # log("Rebuild server: %d"  % ic, end='\r')
        

def StartServer(addr, laddr):
    ic = 0
    bc = 0
    while 1:
        try:
            w = SenderHandler(addr=addr, laddr=laddr)
            # w.handle_build_more(REVERSE_OP)
        except ConnectionRefusedError:
            ic += 1
            log("con : error try again : %d" % ic , end='\r')
            time.sleep(1)
            continue
        try:
            ccc = 0
            while 1:
                ccc += 1
                for i,h in enumerate(SenderHandler.all_sender):
                    try:
                        h.handle()
                        if h.reset:
                            h.unregist_sender()
                            log('[conn  %d/%d]' % (i,ccc), end='\r')
                            
                    except ConnectionRefusedError:
                        log("%s can not connect!" % w.unconnect, end='\r')
                        
                        continue
                if not SenderHandler.all_sender:
                    raise ConnectionResetError()
        except ConnectionResetError:
            bc += 1
            # log("connection break : %d" % bc, end='\r')
            time.sleep(0.01)
            continue


def main():
    cmd = ' '.join(sys.argv[1:])
    try:
        if '-' in cmd:
            l,r = cmd.split('-',1)
            ip,port = r.split(":")
            log("put local's port: %s  ---> connect --> %s:%s" % (l, ip, port))
            StartServer(r.strip(), l.strip())
        else:
            port1,port2 = cmd.split(":")
            log(" %s  <---> connect <--> %s" % (port1, port2))
            ConnectServer(int(port1), int(port2))
    except Exception as e:
        raise e
        log("port -> ip:port  or port1:port2")

if __name__ == '__main__':
    main()