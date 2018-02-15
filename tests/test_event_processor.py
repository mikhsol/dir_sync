import os
from unittest import TestCase
from inotify_simple import flags
from dir_sync.directory_monitor import DirectoryMonitor
from dir_sync.event_processor import EventProcessor, StubSender
from dir_sync.files_comporator import FilesComporator as fc

class EventProcessorTest(TestCase):

    def setUp(self):
        if os.path.isdir('tmp'):
            os.system('rm -r tmp')
        os.mkdir('tmp')
        os.mkdir('tmp/.ds')
        self.m = DirectoryMonitor('tmp', ['tmp/.ds'])
        self.ep = EventProcessor('tmp', StubSender)

    def tearDown(self):
        self.m.close()
        os.system('rm -r tmp')


class FileEventProcessorTest(EventProcessorTest):
    def setUp(self):
        super().setUp()
        os.system('touch tmp/hello.txt')
        self.events = self.m.get_events()
        self.flags_ = self.m.get_flags(self.events[0])
        self.ep.process(self.events[0])


    def test_on_create(self):
        self.assertEqual(len(self.events), 1)
        self.assertIn(flags.CREATE, self.flags_)

        self.assertTrue(os.path.exists('tmp/.ds/hello.txt'))
        self.assertTrue(fc.is_equal('tmp/hello.txt', 'tmp/.ds/hello.txt'))

    def test_on_modify(self):
        os.system('echo hello >> tmp/hello.txt')

        events = self.m.get_events()
        self.assertEqual(len(events), 1)

        flags_ = self.m.get_flags(events[0])
        self.assertIn(flags.MODIFY, flags_)

        self.ep.process(events[0])

        self.assertTrue(os.path.exists('tmp/.ds/hello.txt'))
        self.assertTrue(fc.is_equal('tmp/hello.txt', 'tmp/.ds/hello.txt'))

    def test_on_delete(self):
        os.system('rm tmp/hello.txt')

        events = self.m.get_events()
        self.assertEqual(len(events), 1)

        flags_ = self.m.get_flags(events[0])
        self.assertIn(flags.DELETE, flags_)

        self.ep.process(events[0])

        self.assertFalse(os.path.exists('tmp/hello.txt'))
        self.assertFalse(os.path.exists('tmp/.ds/hello.txt'))


class DirectoryEventProcessorTest(EventProcessorTest):
    def setUp(self):
        super().setUp()
        os.mkdir('tmp/hello')
        self.events = self.m.get_events()
        self.flags_ = self.m.get_flags(self.events[0])
        self.ep.process(self.events[0])

    def test_on_create(self):
        self.assertEqual(len(self.events), 1)
        self.assertIn(flags.CREATE, self.flags_)
        self.assertIn(flags.ISDIR, self.flags_)

        self.ep.process(self.events[0])

        self.assertTrue(os.path.exists('tmp/.ds/hello'))
        self.assertTrue(os.path.isdir('tmp/.ds/hello'))
        self.assertEqual(self.m._get_path_from_event(self.events[0]), 'tmp/hello')
        self.assertEqual(self.events[0].wd, 1)
        self.assertEqual(len(self.m.watched_dirs), 2)
        self.assertEqual(self.m.watched_dirs.get(2).path, 'tmp/hello')

    def test_on_modify_file_in_directory(self):
        # Add file to new directory
        os.system('touch tmp/hello/hello.txt')

        events = self.m.get_events()
        self.assertEqual(len(events), 1)

        flags_ = self.m.get_flags(events[0])
        self.assertIn(flags.CREATE, flags_)

        self.ep.process(events[0])

        self.assertTrue(os.path.exists('tmp/.ds/hello/hello.txt'))
        self.assertTrue(fc.is_equal('tmp/hello/hello.txt', 'tmp/.ds/hello/hello.txt'))

        # Modify file in new directory
        os.system('echo hello >> tmp/hello/hello.txt')

        events = self.m.get_events()
        self.assertEqual(len(events), 1)

        flags_ = self.m.get_flags(events[0])
        self.assertIn(flags.MODIFY, flags_)

        self.ep.process(events[0])

        self.assertTrue(os.path.exists('tmp/.ds/hello/hello.txt'))
        self.assertTrue(fc.is_equal('tmp/hello/hello.txt', 'tmp/.ds/hello/hello.txt'))

        # Delete file in new directory
        os.system('rm tmp/hello/hello.txt')

        events = self.m.get_events()
        self.assertEqual(len(events), 1)

        flags_ = self.m.get_flags(events[0])
        self.assertIn(flags.DELETE , flags_)

        self.ep.process(events[0])

        self.assertFalse(os.path.exists('tmp/hello/hello.txt'))
        self.assertFalse(os.path.exists('tmp/.ds/hello/hello.txt'))

    def test_on_delete(self):
        # Delete directory with file
        os.system('touch tmp/hello/hello.txt')
        events = self.m.get_events()
        self.assertEqual(len(events), 1)
        self.ep.process(events[0])

        os.system('rm -r tmp/hello')

        events = self.m.get_events()
        self.assertEqual(len(events), 3)

        for event in events:
            self.ep.process(event)

        self.assertFalse(os.path.exists('tmp/hello'))
        self.assertFalse(os.path.exists('tmp/.ds/hello'))
        self.assertFalse(os.path.exists('tmp/hello/hello.txt'))
        self.assertFalse(os.path.exists('tmp/.ds/hello/hello.txt'))
