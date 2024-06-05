import logging
from flask_socketio import SocketIO

class SocketIOHandler(logging.Handler):
    def __init__(self, socketio):
        logging.Handler.__init__(self)
        self.socketio = socketio

    def emit(self, record):
        log_entry = self.format(record)
        self.socketio.emit('log', {'data': log_entry})

def setup_logger(socketio):
    logger = logging.getLogger('crew_logger')
    logger.setLevel(logging.DEBUG)
    handler = SocketIOHandler(socketio)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
