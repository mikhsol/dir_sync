from unittest import TestCase
import os

from dsync_cl import prepare_directory


class PrepareDirectoryFunctionTest(TestCase):

    def test_on_non_existed_directory(self):
        dir_name = 'tmpt'

        prepare_directory(dir_name)

        self.assertTrue(os.path.exists(dir_name))
        self.assertTrue(os.path.isdir(dir_name))

        self.assertTrue(os.path.exists(dir_name+'/.ds'))
        self.assertTrue(os.path.isdir(dir_name+'/.ds'))

        os.system('rm -rf '+dir_name)

    def test_on_non_empty_directory(self):
        dir_name = 'tmp'

        os.mkdir(dir_name)
        os.system('touch tmp/1.txt')
        os.system('touch tmp/2.txt')
        os.mkdir('tmp/tst')
        os.system('touch tmp/tst/1.txt')
        os.system('touch tmp/tst/2.txt')

        prepare_directory(dir_name)

        self.assertTrue(os.path.exists(dir_name))
        self.assertTrue(os.path.isdir(dir_name))

        self.assertTrue(os.path.exists(dir_name+'/.ds'))
        self.assertTrue(os.path.isdir(dir_name+'/.ds'))

        self.assertEqual(len(os.listdir('tmp/.ds')), 3)
        self.assertEqual(len(os.listdir('tmp/.ds/tst')), 2)

        os.system('rm -rf '+dir_name)
