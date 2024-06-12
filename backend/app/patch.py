import eventlet
eventlet.monkey_patch()

# Apply specific patches or compatibility fixes
import sys
import select

# Mock the select.epoll if not available
if not hasattr(select, 'epoll'):
    class epoll:
        def __init__(self):
            self.fds = {}
        def fileno(self):
            return -1
        def close(self):
            pass
        def register(self, fd, eventmask):
            self.fds[fd] = eventmask
        def modify(self, fd, eventmask):
            self.fds[fd] = eventmask
        def unregister(self, fd):
            self.fds.pop(fd, None)
        def poll(self, timeout=None):
            return []
    select.epoll = epoll

# Make sure eventlet patches everything necessary
eventlet.monkey_patch(os=False, select=True)

# Add missing methods to GreenSocket
import eventlet.green.socket as green_socket

if not hasattr(green_socket.GreenSocket, 'sendmsg'):
    def sendmsg(self, *args, **kwargs):
        raise NotImplementedError("sendmsg is not supported by eventlet's GreenSocket")
    green_socket.GreenSocket.sendmsg = sendmsg

if not hasattr(green_socket.GreenSocket, 'recvmsg'):
    def recvmsg(self, *args, **kwargs):
        raise NotImplementedError("recvmsg is not supported by eventlet's GreenSocket")
    green_socket.GreenSocket.recvmsg = recvmsg

if not hasattr(green_socket.GreenSocket, 'recvmmsg'):
    def recvmmsg(self, *args, **kwargs):
        raise NotImplementedError("recvmmsg is not supported by eventlet's GreenSocket")
    green_socket.GreenSocket.recvmmsg = recvmmsg

if not hasattr(green_socket.GreenSocket, 'sendmmsg'):
    def sendmmsg(self, *args, **kwargs):
        raise NotImplementedError("sendmmsg is not supported by eventlet's GreenSocket")
    green_socket.GreenSocket.sendmmsg = sendmmsg