import filecmp
import difflib


class FilesComporator:
    @staticmethod
    def is_equal(one, two):
        return filecmp.cmp(one, two, shallow=False)

    @staticmethod
    def diff(one, two):
        '''Return how file two differ of file one'''
        result = []
        if FilesComporator.is_equal(one, two):
            return result
        o, t = [], []
        with open(one, 'rb') as f1:
            o = f1.read()
        with open(two, 'rb') as f2:
            t = f2.read()

        matcher = difflib.SequenceMatcher(None, o, t)
        for tag, i1, i2, j1, j2 in reversed(matcher.get_opcodes()):
            result.append({
                'tag': tag,
                'i1': i1, 'i2': i2,
                'payload': t[j1: j2]
                })

        return result

    @staticmethod
    def patch(file, diff):
        '''Patch file with provided diff rules given by difflib.SequenceMatcher
           opcodes (rules how to turn one object into another)
        '''
        if len(diff) == 0:
            return
        data = []
        with open(file, 'rb') as f:
            data = bytearray(f.read())

        for d in diff:
            tag, payload = d['tag'], d['payload']
            i1, i2 = d['i1'], d['i2']

            if tag in ['insert', 'replace']:
                data[i1:i2] = payload
            elif tag == 'delete':
                del data[i1:i2]
            elif tag == 'equal':
                continue

        with open(file, 'wb') as f:
            f.write(data)
