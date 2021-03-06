import os
from unittest import TestCase
from files_comporator import FilesComporator as fc


class FilesComporatorTest(TestCase):

    def setUp(self):
        if os.path.isdir('tmp'):
            os.system('rm -r tmp')
        self.file1 = 'tmp/file1.txt'
        self.file2 = 'tmp/file2.txt'

        os.mkdir('tmp')

    def tearDown(self):
        os.system('rm -rf tmp')

    def test_compare_two_empty_files(self):
        os.system('echo > ' + self.file1)
        os.system('echo >' + self.file2)

        self.assertTrue(fc.is_equal(self.file1, self.file2))
        self.assertEqual(len(fc.diff(self.file1, self.file2)), 0)

    def test_compare_empty_and_non_empty_file_get_diff_patch_first_file(self):
        os.system('echo >' + self.file1)
        os.system('echo hello > ' + self.file2)

        diff = fc.diff(self.file1, self.file2)
        self.assertFalse(fc.is_equal(self.file1, self.file2))
        self.assertEqual(len(diff), 1)

        os.system('echo world >> ' + self.file2)
        diff = fc.diff(self.file1, self.file2)
        self.assertFalse(fc.is_equal(self.file1, self.file2))
        self.assertEqual(len(diff), 2)

        fc.patch(self.file1, diff)
        self.assertTrue(fc.is_equal(self.file1, self.file2))

    def test_replace_and_delete_in_files_for_patch(self):
        os.system('echo hello >' + self.file1)
        os.system('echo awful >>' + self.file1)
        os.system('echo world >>' + self.file1)
        os.system('echo haaaa!! >> ' + self.file1)

        os.system('echo hello > ' + self.file2)
        os.system('echo great >> ' + self.file2)
        os.system('echo my >> ' + self.file2)
        os.system('echo world >> ' + self.file2)

        diff = fc.diff(self.file1, self.file2)
        self.assertFalse(fc.is_equal(self.file1, self.file2))
        self.assertEqual(len(diff), 3)

        fc.patch(self.file1, diff)
        self.assertTrue(fc.is_equal(self.file1, self.file2))
