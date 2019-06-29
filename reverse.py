#!/bin/python
# from argparse import ArgumentParser
import socket
import traceback
from socket import SO_REUSEADDR, SO_REUSEPORT, SOL_SOCKET
from socket import AF_INET, SOCK_STREAM
import sys 
import select
import time
import argparse
# import pdb
PY = int(sys.version[0])
if PY == 2:
    class ConnectionResetError(socket.error):pass
    class ConnectionRefusedError(socket.error):pass
    class BrokenPipeError(socket.error):pass

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
    #sock.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
    sock.listen(15)
    while 1:
        s,_ = sock.accept()
        yield s

def log(i, end='\n'):
    if PY ==3 and isinstance(i,bytes):
        sys.stdout.write(str(i)+end)
    else:
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
        if not addr:
            self.addr = 'localhost:12364'
        if not laddr:
            self.laddr = 'localhost:12365'
        self.to_ldata = b''
        self.to_rdata = b''
        self.unconnect = ''
        self.reset = False
        self._alive_interval = alive_check_sec
        self.start_time = time.time()
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
        if PY == 2:
            try:
                fn = sock.fileno()
            except socket.error:
                fn = -1
        else:
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
        self._ = time.time()
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
        
        #log("data: r[%s] l[%s]" % (self.to_rdata, self.to_ldata) ,end='\r')
        for s in wl:
            if len(self.to_rdata) > 0 and s is self.sock:
                #log(" --> local")
                self.handle_write(s)
            if len(self.to_ldata) > 0 and s is self.lsock:
                #log(" --> remote")
                self.handle_write(s)

        self.clean
        # log("reset : %s" % self.reset,end='\r')

    def handle_error(self, sock):
        sock.close()
        self.unregist_sock(sock)
        """if sock != self.lsock and self.lsock:
            self.lsock.close()
            self.unregist_sock(self.lsock)"""
        if hasattr(self,'lsock') and sock != self.lsock and self.lsock:
            self.lsock.close()
            self.unregist_sock(self.lsock)
        #else:
        #    self.unregist_sock(self.sock)
        self.reset = True
        self.unregist_sender()

    def handle_build_more(self, d):
        d = _extract(d, REVERSE_OP)
        ## connection more conn
        
        SenderHandler(addr=self.addr, laddr=self.laddr)
        SenderHandler(addr=self.addr, laddr=self.laddr)
        log("reverse connection: %d"% len(self.__class__.all_sender), end='\r')
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
            if REVERSE_OP in d:
                #log("from : %s " %(self.addr))
                d = self.handle_build_more(d)
                #import pdb;pdb.set_trace()
                if not d:
                    return
            self.to_ldata += d
            if not self.lsock:
                self.lsock = self.create_sock(self.laddr)
                self.regist_sock(self.lsock)
        elif sock == self.lsock:
            #log("from : %s" %self.laddr)
            self.to_rdata += d

        #log("data:[%s] [%s] [%s]" % (d,self.to_rdata, self.to_ldata) )
    
        

    def handle_write(self, sock):
        dirty = False
        try:
            if sock == self.sock and self.to_rdata:
                sn = sock.send(self.to_rdata)
                # print(self.to_rdata)
                #log(self.to_rdata)
                #log("reverse <- %d " % sn, end='\n')

                self.to_rdata = self.to_rdata[sn:]
                if self.to_rdata:
                    dirty = True
            elif sock == self.lsock and self.to_ldata:
                sn = sock.send(self.to_ldata)
                # print(self.to_ldata)
                #log(self.to_ldata)
                #log("reverse -> %d  " % sn, end='\n')
                self.to_ldata = self.to_ldata[sn:]
                if self.to_ldata:
                    dirty = True
            
        except BrokenPipeError as e:
            log("socks break ! . reset")
            self.handle_error(sock)
            dirty = False
        except socket.error as e:
            if e.errno == socket.errno.EBADF:
                log("socks break ! . reset")
            else:
                log("sockset: %s " % e)
            self.handle_error(sock)
            dirty = False
        except Exception as e:
            log("0999")


        #if dirty:
        #    self.handle_write(sock)

    def check_alive(self, sock):
        r,w, _ = select.select([sock], [], [], 1)
        if len(r) > 0:
            d = r[0].recv(9216)
            if not d:
                log("check alive [x] ")
                self.handle_error(sock)
                return False
            if sock == self.sock:
                self.to_ldata += d
            else:
                self.to_rdata += d

    def create_sock(self, addr, block=False, try_time=4):
        #log("build sock: %s" %addr)
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
        try:
            sock.connect((ip, port))
        except socket.gaierror as e:
            log("try conn -> %s:%d [x]"%(ip, port))
            if try_time == 0:
                log("[261] :%s" % e)
                raise e
            else:
                return self.create_sock(addr,block,try_time=try_time-1)

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
                    log("connection break %r" % hand)
                    un_r.append(hand)
            except socket.error as e:
                if socket.errno.EBADF != e.errno:
                    log("[337] %s " % e)


        
        # clear break connection
        for u in un_r:
            self._runing_handlers.remove(u)

        if need_conn_num > 0 and len(self._runing_handlers) > 0:
            #log("send cmd to create more conec", end='\r')
            h = self._runing_handlers[0]
            h.to_ldata += REVERSE_OP
            h.handle_write(h.lsock)
                
    def handle_check_alive(self):
        al_s = self.recv_list
        rl, _ ,_ = select.select(al_s, [], [], 0.001)
        for s in rl:
            d = s.recv(1024)
            if not d:
                self.handle_error(s)
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
    try:
        while 1: 
            ic +=1
            R.handle()
    except Exception as e:
        print(e)
            
        # log("Rebuild server: %d"  % ic, end='\r')
        

def StartServer(addr, laddr):
    ic = 0
    bc = 0
    conn_err_t = 0
    while 1:
        try:
            w = SenderHandler(addr=addr, laddr=laddr)
            # w.handle_build_more(REVERSE_OP)
            conn_err_t = 0
        except ConnectionRefusedError as e:
            log("[406] %s"% str(e))
            ic += 1
            log("con : error try again : %d" % ic , end='\r')
            time.sleep(1 + conn_err_t % 30)
            conn_err_t += 1
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
                    #raise ConnectionResetError()
                    continue
        except ConnectionResetError:
            bc += 1
            # log("connection break : %d" % bc, end='\r')
            time.sleep(0.01)
            continue


def get_config():
    parser = argparse.ArgumentParser()
    parser.add_argument('-B', '--build', default='40001:40002', help='build [listen port1] < -- >  [listen port2] exm: port1:port2 ')
    parser.add_argument('-l', '--local', default=None, help='example: localserver:port1 connect local port must use with -r : connect to remote port ')
    parser.add_argument('-r', '--remote', default=None, help='example: remoteserver:port2 connect to remote port ')
    args = parser.parse_args()
    if args.local:
        assert args.remote != None
        if ':' not in args.local:
            l_port = int(args.local)
            l = 'localhost:%d' % l_port
        else:
            l = args.local

        if ':' in args.remote:
            r = args.remote
        else:
            r_port = int(args.remote)
            r = 'localhost:%d' % r_port
        log("put local's port: %s  ---> connect --> %s" % (l,r))
        StartServer(r.strip(), l.strip())

    else:
        try:
            assert ":" in args.build
            port1,port2 = args.build.split(":")
            log(" %s  <---> connect <--> %s" % (port1, port2))
            ConnectServer(int(port1), int(port2))
        except Exception as e:
            log("err bye : %s" % str(e) )




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

if __name__ == '__main__':
    get_config()
    #main()
