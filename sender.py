import socket
import os
import logging
import pickle

from utils import SocketEvents as se

logger = logging.getLogger('client')


class AbstractSenderStrategy:

    def send_file(self, file_path, file_name):
        raise NotImplemented

    def send_directory(self, directory):
        raise NotImplemented

    def send_event(self, event):
        raise NotImplemented


class StubSender(AbstractSenderStrategy):

    def send_file(self, file_path, file_name):
        pass

    def send_directory(self, path):
        pass

    def send_event(self, event):
        pass


class SocketSender(AbstractSenderStrategy):
    MSG_SIZE = 1024

    def __init__(self, host='localhost', port='6666'):
        self.host = host
        self.port = port

    def init(self, directory):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            s.send(se.INIT)
            status = s.recv(self.MSG_SIZE)
            if status == se.READY:
                s.send(bytearray(directory, 'utf-8'))
                status = s.recv(self.MSG_SIZE)
                if status == se.OK:
                    logger.info('Root directory name was sent...')
                else:
                    # TODO: rise DataTransferError
                    pass

        self.send_directory(directory)
        logger.info('Init success...')


    def send_file(self, file_path, file_name):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            s.send(se.FILE)
            status = s.recv(self.MSG_SIZE)
            if status == se.READY:
                file_ = os.path.join(file_path, file_name)
                if not os.path.exists(file_):
                    logger.error('No such file "{}"'.format(file_))
                    # TODO: raise NoSuchFileException
                if not os.path.isfile(file_):
                    logger.error('Not a file "{}"'.format(file_))
                    # TODO: raise NotAFileException
                logger.info('Server ready to receive' +
                            'file: "{}", start transmition.'.format(file_))
                s.send(bytearray(file_path, 'utf-8'))
                s.send(bytearray(file_name, 'utf-8'))
                with open(file_path, 'rb') as f:
                    d = f.read(self.MSG_SIZE)
                    while d:
                        s.send(d)
                        d = f.read(self.MSG_SIZE)
                status = s.recv(self.MSG_SIZE)
                if status == se.OK:
                    logger.info('File "{}" was delivered.'.format(file_name))
                # conn.send(se.FINISH)
                else:
                    # TODO: rise FileTransferError
                    pass
            else:
                logger.error('Does not support such server response "{}"'
                             .format(str(status)))
                raise NotImplementedError

    def send_directory(self, path):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            s.send(se.DIRECTORY)
            status = s.recv(self.MSG_SIZE)
            if status == se.READY:
                if not os.path.exists(path):
                    logger.error('No such directory "{}"'.format(path))
                    # TODO: raise NoSuchDirectoryException
                if not os.path.isdir(path):
                    logger.error('Not a directory "{}"'.format(path))
                    raise NotADirectoryError
                logger.info('Send path to remote host...')
                s.send(bytearray(path, 'utf-8'))
                status = s.recv(self.MSG_SIZE)
                if status == se.OK:
                    logger.info('Directory was created on remote host...')
                else:
                    # TODO: rise DataTransferError
                    pass
            else:
                logger.error('Does not support such server response "{}"'
                             .format(str(status)))
                raise NotImplementedError

        for el in os.listdir(path):
            el_path = os.path.join(path, el)
            if os.path.isdir(el_path):
                self.send_directory(el_path)
            elif os.path.isfile(el_path):
                self.send_file(el_path, el)
            else:
                logger.warning('Does not support type of "{}"'.format(el_path))

    def send_event(self, event):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            s.send(se.EVENT)
            status = s.recv(self.MSG_SIZE)
            if status == se.READY:
                s.sendall(pickle.dumps(event))
                status = s.recv(self.MSG_SIZE)
                if status == se.OK:
                    logger.info('Event was sent to remote host...')
                else:
                    # TODO: rise DataTransferError
                    pass
            else:
                logger.error('Does not support such server response "{}"'
                             .format(str(status)))
                raise NotImplementedError
