import os
import socket
import pickle
import logging

from utils import SocketEvents as se, create_logger
from event_processor import ServerEventProcessor

logger = logging.getLogger('server')


class SocketReceiver:
    MSG_SIZE = 1024
    TRACKING_DIRS = 'tracking_dirs'

    def __init__(self, host='localhost', port='6666'):
        self.host = host
        self.port = port
        self.sock = socket.socket()
        self.sock.bind((self.host, self.port))
        self.sock.listen(1)
        self.ep = None

    def handle(self):
        try:
            logger.info('Wait for new connection...')
            conn, addr = self.sock.accept()
            event = conn.recv(self.MSG_SIZE)
            if event == se.INIT:
                conn.send(se.READY)
                logger.info('Ready to receive init directory...')
                dir_name = os.path.join(self.TRACKING_DIRS,
                                        str(conn.recv(self.MSG_SIZE)))
                logger.info('Init directory: {}'.format(dir_name))
                self.ep = ServerEventProcessor(dir_name)
            elif event == se.FILE:
                conn.send(se.READY)
                logger.info('Ready to receive file...')
                file_path = os.path.join(self.TRACKING_DIRS,
                                         str(conn.recv(self.MSG_SIZE)))
                logger.info('File path: {}'.format(file_path))
                file_name = str(conn.recv(self.MSG_SIZE))
                logger.info('File name: {}'.format(file_name))
                if not os.path.exists(file_path):
                    os.makedirs(file_path, exist_ok=True)
                file_ = os.path.join(file_path, file_name)
                os.system('touch '.format(file_))
                logger.info('File {} was created'.format(file_name))
                with open(file_, 'wb') as f:
                    d = conn.recv(self.MSG_SIZE)
                    while d:
                        f.write(d)
                        d = conn.recv(self.MSG_SIZE)
                logger.info('File {} was deliverd.'.format(file_name))
            elif event == se.DIRECTORY:
                conn.send(se.READY)
                logger.info('Ready to receive new directory path...')
                path = str(conn.recv(self.MSG_SIZE))
                path = os.path.join(self.TRACKING_DIRS, path)
                if not os.path.exists(path):
                    os.makedirs(path, exist_ok=True)
                    logger.info('New directory {} was created.'.format(path))
                logger.info('Directory {} already exists.'.format(path))
            elif event == se.EVENT:
                conn.send(se.READY)
                logger.info('Ready to receive new event...')
                data = b''
                d = conn.recv(self.MSG_SIZE)
                while d:
                    data += d
                    d = conn.recv(self.MSG_SIZE)
                event = pickle.loads(data)
                self.ep.process(event)
            else:
                # TODO: NoSuchEventException
                pass

            conn.send(se.OK)
        finally:
            conn.close()
