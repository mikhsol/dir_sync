import os
from distutils.dir_util import copy_tree
from inotify_simple import flags
from files_comporator import FilesComporator as fc


class EventProcessor:

    def process(self, event):
        raise NotImplementedError


class ClientEventProcessor(EventProcessor):
    DS_DIR = '.ds'

    def __init__(self, directory=None, sender=None):
        if not directory:
            # TODO: create proper exception class
            raise NotADirectoryError
        self.directory = directory
        self.ds_path = os.path.join(directory, self.DS_DIR)
        if not os.path.isdir(self.ds_path):
            os.mkdir(self.ds_path)
        self.sender = sender

    def process(self, event):
        flags_ = flags.from_mask(event.mask)
        # Generate path to local copy for new object to have chance
        # get changes on object modify event later.
        ds_path_to_new_object = \
            os.path.join(self.ds_path,
                         event.directory.path[len(self.directory)+1:])

        if flags.ISDIR in flags_:
            if flags.CREATE in flags_:
                copy_tree(event.directory.path, ds_path_to_new_object)
                self.sender.send_directory(event.directory.path)
            elif flags.DELETE in flags_:
                path_to_delete = os.path.join(ds_path_to_new_object,
                                              event.name)
                os.system('rm -r {}'.format(path_to_delete))
                self.sender.send_event(event)
            else:
                # TODO: add proper exception
                raise NotImplemented
        else:
            file_path = os.path.join(event.directory.path, event.name)
            ds_file_path = os.path.join(ds_path_to_new_object, event.name)
            if flags.CREATE in flags_:
                if not os.path.exists(ds_path_to_new_object):
                    os.mkdir(ds_path_to_new_object)
                os.system('cp {} {}'.format(file_path, ds_file_path))
                self.sender.send_file(event.directory.path, event.name)
            elif flags.MODIFY in flags_:
                diff = fc.diff(ds_file_path, file_path)
                fc.patch(ds_file_path, diff)
                event.diff = diff
                self.sender.send_event(event)
            elif flags.DELETE in flags_:
                if os.path.exists(ds_file_path):
                    os.system('rm {}'.format(ds_file_path))
                self.sender.send_event(event)
            elif flags.IGNORED in flags_:
                # IGNORED flag automatically generated on delete event, do not
                # need to process it.
                pass
            else:
                # TODO: add proper exception
                raise NotImplemented


class ServerEventProcessor(EventProcessor):

    def __init__(self, directory=None):
        if not directory:
            # TODO: raise NoSuchDirectoryException
            pass
        self.directory = directory
        if not os.path.exists(self.directory):
            os.makedirs(self.directory, exist_ok=True)

    def process(self, event):
        flags_ = flags.from_mask(event.mask)

        if flags.ISDIR in flags_:
            if flags.DELETE in flags_:
                if os.path.exists(event.directory.path):
                    os.system('rm -r {}'.format(event.directory.path))
            else:
                # TODO: add proper exception
                raise NotImplemented
        else:
            path = os.path.join(event.directory.path, event.name)
            if flags.MODIFY in flags_:
                fc.patch(path, event.diff)
            elif flags.DELETE in flags_:
                if os.path.exists(path):
                    os.system('rm {}'.format(path))
            else:
                # TODO: add proper exception
                raise NotImplemented
