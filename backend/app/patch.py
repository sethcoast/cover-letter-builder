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
