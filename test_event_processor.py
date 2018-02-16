import os
from unittest import TestCase
from inotify_simple import flags
from directory_monitor import DirectoryMonitor, EventInfo
from event_processor import ClientEventProcessor, ServerEventProcessor
from sender import StubSender
from files_comporator import FilesComporator as fc


class EventProcessorTest(TestCase):
    def setUp(self):
        if os.path.isdir('tmp'):
            os.system('rm -r tmp')
        os.mkdir('tmp')
        os.mkdir('tmp/.ds')
        self.m = DirectoryMonitor('tmp', ['tmp/.ds'])

    def tearDown(self):
        os.system('rm -r tmp')
        self.m.close()


class ClientEventProcessorTest(EventProcessorTest):

    def setUp(self):
        super().setUp()
        self.ep = ClientEventProcessor('tmp', StubSender())

    def tearDown(self):
        super().tearDown()


class ClientFileEventProcessorTest(ClientEventProcessorTest):
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


class ClientDirectoryEventProcessorTest(ClientEventProcessorTest):
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
        self.assertEqual(self.m._get_path_from_event(self.events[0]),
                         'tmp/hello')
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
        self.assertTrue(fc.is_equal('tmp/hello/hello.txt',
                                    'tmp/.ds/hello/hello.txt'))

        # Modify file in new directory
        os.system('echo hello >> tmp/hello/hello.txt')

        events = self.m.get_events()
        self.assertEqual(len(events), 1)

        flags_ = self.m.get_flags(events[0])
        self.assertIn(flags.MODIFY, flags_)

        self.ep.process(events[0])

        self.assertTrue(os.path.exists('tmp/.ds/hello/hello.txt'))
        self.assertTrue(fc.is_equal('tmp/hello/hello.txt',
                                    'tmp/.ds/hello/hello.txt'))

        # Delete file in new directory
        os.system('rm tmp/hello/hello.txt')

        events = self.m.get_events()
        self.assertEqual(len(events), 1)

        flags_ = self.m.get_flags(events[0])
        self.assertIn(flags.DELETE, flags_)

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


class ServerEventProcessorTest(EventProcessorTest):

    def setUp(self):
        super().setUp()
        self.ep = ServerEventProcessor('tmp')
        self.cep = ClientEventProcessor('tmp', StubSender())

    def tearDown(self):
        super().tearDown()

    def process_dummy_events(self):
        events = self.m.get_events()
        # Need to do this to allow client make correct manipulation with
        # .ds dir
        for event in events:
            self.cep.process(event)
        return events


class ServerFileEventProcessorTest(ServerEventProcessorTest):

    def test_on_server_event_processor_init(self):
        self.ep = ServerEventProcessor('tmp_srv')
        self.assertTrue(os.path.exists('tmp_srv'))
        self.assertTrue(os.path.isdir('tmp_srv'))
        os.system('rm -r tmp_srv')

    def test_on_modify(self):
        os.system('echo hello > tmp/hello.txt')
        events = self.process_dummy_events()
        self.assertEqual(len(events), 2)

        os.system('mv tmp/hello.txt tmp/hello_check.txt')
        os.system('touch tmp/hello.txt')
        diff = fc.diff('tmp/hello.txt', 'tmp/.ds/hello.txt')
        event = events[1]
        event.diff = diff
        self.ep.process(event)

        self.assertTrue(fc.is_equal('tmp/hello.txt', 'tmp/hello_check.txt'))

    def test_on_delete(self):
        os.system('echo hello > tmp/hello.txt')
        events = self.process_dummy_events()
        self.assertEqual(len(events), 2)

        os.system('rm tmp/hello.txt')
        events = self.process_dummy_events()
        self.assertEqual(len(events), 1)

        os.system('echo hello > tmp/hello.txt')
        self.ep.process(events[0])

        self.assertFalse(os.path.exists('tmp/hello.txt'))


class ServerDirectoryEventProcessorTest(ServerEventProcessorTest):

    def test_on_delete(self):
        os.mkdir('tmp/hello')
        events = self.process_dummy_events()
        self.assertEqual(len(events), 1)

        os.system('rm -r tmp/hello')
        events = self.process_dummy_events()
        self.assertEqual(len(events), 2)

        os.mkdir('tmp/hello')
        self.ep.process(events[1])

        self.assertFalse(os.path.exists('tmp/hello'))
