import socket
import os
import logging
import pickle

from utils import SocketEvents as se

logger = logging.getLogger('client')


class DataTransferError(Exception):
    pass


class NoSuchFileError(Exception):
    pass


class NoSuchDirectoryError(Exception):
    pass


class NotAFileException(Exception):
    pass


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

    def __init__(self, host='localhost', port='6666', excluded_dirs=[]):
        self.host = host
        self.port = port
        self.excluded_dirs = excluded_dirs

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
                    logger.error('Unexpected staus "{}" was returned.'
                                 .format(status))
                    raise DataTransferError

        self.send_directory(directory)
        logger.info('Init success...')

    def send_file(self, file_path, file_name):
        file_ = os.path.join(file_path, file_name)
        if not os.path.exists(file_):
            logger.error('No such file "{}"'.format(file_))
            raise NoSuchFileError
        if not os.path.isfile(file_):
            logger.error('Not a file "{}"'.format(file_))
            raise NotAFileException

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            s.send(se.FILE)
            status = s.recv(self.MSG_SIZE)
            if status == se.READY:
                logger.info('Server ready to receive ' +
                            'file: "{}", start transmition.'.format(file_))
                s.send(bytearray(file_path, 'utf-8'))
                status = s.recv(self.MSG_SIZE)
                if status == se.READY:
                    s.send(bytearray(file_name, 'utf-8'))
                status = s.recv(self.MSG_SIZE)
                if status == se.READY:
                    with open(file_, 'rb') as f:
                        d = f.read(self.MSG_SIZE)
                        while d:
                            s.send(d)
                            d = f.read(self.MSG_SIZE)
                s.send(se.FINISHED)
                status = s.recv(self.MSG_SIZE)
                if status == se.OK:
                    logger.info('File "{}" was delivered.'.format(file_name))
                else:
                    logger.error('File "{}" was not delivered.'
                                 .format(file_name))
                    raise DataTransferError
            else:
                logger.error('Does not support such server response "{}"'
                             .format(str(status).decode('utf-8')))
                raise NotImplementedError

    def send_directory(self, path):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            s.send(se.DIRECTORY)
            status = s.recv(self.MSG_SIZE)
            if status == se.READY:
                if not os.path.exists(path):
                    logger.error('No such directory "{}"'.format(path))
                    raise NoSuchDirectoryError
                if not os.path.isdir(path):
                    logger.error('Not a directory "{}"'.format(path))
                    raise NotADirectoryError
                logger.info('Send path to remote host...')
                s.send(bytearray(path, 'utf-8'))
                status = s.recv(self.MSG_SIZE)
                if status == se.OK:
                    logger.info('Directory was created on remote host...')
                else:
                    logger.error('Unexpected staus "{}" was returned.'
                                 .format(status))
                    raise DataTransferError
            else:
                logger.error('Does not support such server response "{}"'
                             .format(str(status)))
                raise NotImplementedError

        for el in os.listdir(path):
            el_path = os.path.join(path, el)
            if os.path.isdir(el_path) and el_path not in self.excluded_dirs:
                self.send_directory(el_path)
            elif os.path.isfile(el_path):
                self.send_file(path, el)
            elif el_path not in self.excluded_dirs:
                logger.warning('Does not support type of "{}"'.format(el_path))

    def send_event(self, event):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            s.send(se.EVENT)
            status = s.recv(self.MSG_SIZE)
            if status == se.READY:
                logger.info('Start send event {}...'.format(event))
                data = pickle.dumps(event)
                msg_idx = 0
                end_idx = 0
                while end_idx < len(data):
                    start_idx = msg_idx * self.MSG_SIZE
                    end_idx = (msg_idx + 1) * self.MSG_SIZE
                    s.send(data[start_idx:end_idx])
                    msg_idx += 1
                s.send(se.FINISHED)
                status = s.recv(self.MSG_SIZE)
                if status == se.OK:
                    logger.info('Event was sent to remote host...')
                else:
                    logger.error('Unexpected staus "{}" was returned.'
                                 .format(status))
                    raise DataTransferError
            else:
                logger.error('Does not support such server response "{}"'
                             .format(str(status)))
                raise NotImplementedError
