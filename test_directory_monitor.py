from unittest import TestCase
import os

from inotify_simple import flags

from directory_monitor import DirectoryMonitor


def get_event_and_flags(monitor):
    event = monitor.get_events()[0]
    return event, monitor.get_flags(event)


class DirectoryMonitorTest(TestCase):

    def setUp(self):
        self.path_name = 'tmp'
        if os.path.isdir(self.path_name):
            os.system('rm -r '+self.path_name)
        os.mkdir(self.path_name)
        self.m = DirectoryMonitor(self.path_name)

    def tearDown(self):
        os.system('rm -r '+self.path_name)
        self.m.close()

    def test_no_events(self):
        self.assertEqual(len(self.m.get_events()), 0)

    def test_create_file_in_directory_and_modify_and_delet(self):
        # CREATE
        os.system('echo hello > tmp/test.txt')
        event, flags_ = get_event_and_flags(self.m)

        self.assertEqual(event.name, 'test.txt')
        self.assertEqual(flags_[0], flags.CREATE)

        # MODIFY
        os.system('echo world >> tmp/test.txt')
        event, flags_ = get_event_and_flags(self.m)

        self.assertEqual(event.name, 'test.txt')
        self.assertEqual(flags_[0], flags.MODIFY)

        # DELETE
        os.system('rm tmp/test.txt')
        event, flags_ = get_event_and_flags(self.m)

        self.assertEqual(event.name, 'test.txt')
        self.assertEqual(flags_[0], flags.DELETE)

    def test_add_subdirectory_create_modify_file_delete_subdirectory(self):
        # CREATE DIRECTORY
        os.mkdir(self.path_name+'/foo')
        events = self.m.get_events()

        self.assertEqual(len(events), 1)

        flags_ = self.m.get_flags(events[0])
        self.assertEqual(events[0].name, 'foo')
        for flag in flags_:
            self.assertIn(flag, [flags.CREATE, flags.ISDIR])

        # CREATE FILE
        os.system('echo hello > tmp/foo/test.txt')
        # MODIFY FILE
        os.system('echo world >> tmp/foo/test.txt')
        # DELETE DIRETCTORY
        os.system('rm -r tmp/foo/')

        events = self.m.get_events()
        self.assertEqual(len(events), 4)

        flag = self.m.get_flags(events[0])
        self.assertEqual(events[0].name, 'test.txt')
        self.assertEqual(flag[0], flags.CREATE)

        flag = self.m.get_flags(events[1])
        self.assertEqual(events[1].name, 'test.txt')
        self.assertEqual(flag[0], flags.MODIFY)

        flags_ = self.m.get_flags(events[3])
        self.assertEqual(events[3].name, 'foo')
        for flag in flags_:
            self.assertIn(flag, [flags.DELETE, flags.ISDIR])
        print(events)
        self.assertEqual(events[3].directory.name, 'foo')
        self.assertEqual(events[3].directory.path, 'tmp/foo')
