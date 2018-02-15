import os
from inotify_simple import INotify, flags


class Directory:

    def __init__(self, name, path=None):
        self.wd = None
        self.name = name
        if not path:
            self.path = name
        else:
            self.path = path

    def __str__(self):
        return 'name: {} - path: {}'.format(self.name, self.path)

    def __repr__(self):
        return 'name: {} - path: {}'.format(self.name, self.path)


# TODO: maybe a good idea to separate Directory and File events info as
# ancestor classes of events info.
class EventInfo:

    def __init__(self, event, directory=None):
        self.wd = event.wd
        self.mask = event.mask
        self.cookie = event.cookie
        self.name = event.name
        self.directory = directory

    def __str__(self):
        return 'wd: {} - name: {}'.format(self.wd, self.name)

    def __repr__(self):
        return 'wd: {} - name: {}'.format(self.wd, self.name)


class DirectoryMonitor:

    def __init__(self, root_dir=None, excluded_dirs=[]):
        if not root_dir:
            # TODO: create proper exception class
            raise NotADirectoryError
        self.root_dir = Directory(root_dir)
        self.excluded_dirs = excluded_dirs
        self.inotify = INotify()
        self.watch_flags = flags.CREATE | flags.MODIFY | flags.DELETE
        self.watched_dirs = {}
        self.watch(self.root_dir)

    def watch(self, directory):
        self._init_child_directories(directory)
        directory.wd = self.inotify.add_watch(directory.path, self.watch_flags)
        self.watched_dirs[directory.wd] = directory

    def _init_child_directories(self, directory):
        for file_ in os.listdir(directory.path):
            p = os.path.join(directory.path, file_)
            if os.path.isdir(p) and p not in self.excluded_dirs:
                p = os.path.join(directory.path, file_)
                d = Directory(file_, p)
                self.watch(d)

    def _stop_watch(self, event):
        self.inotify.rm_watch(event.wd)
        return self.watched_dirs.pop(event.wd)

    def close(self):
        self.inotify.close()

    def get_events(self):
        return self._prepare_events(self.inotify.read(timeout=100))

    def _get_path_from_event(self, event):
        path = self.watched_dirs.get(event.wd).path
        if flags.ISDIR in self.get_flags(event):
            path = os.path.join(path, event.name)
        return path

    def _prepare_events(self, events):
        results = []
        for event in events:
            event = EventInfo(event)
            flags_ = self.get_flags(event)
            event.directory = Directory(event.name,
                                        self._get_path_from_event(event))
            if flags.CREATE in flags_ and flags.ISDIR in flags_:
                    self.watch(event.directory)
            elif flags.DELETE in flags_ and flags.ISDIR in flags_:
                    event.directory = self._stop_watch(event)
            results.append(event)
        return results

    @staticmethod
    def get_flags(event):
        return flags.from_mask(event.mask)
