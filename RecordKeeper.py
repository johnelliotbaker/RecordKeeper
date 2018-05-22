import argparse
import hashlib
import glob
import os
from os.path import join as pjoin
import shutil


N_MAX_CHUNKS = 60
ALLOWED_FILETYPES = ['mkv', 'mp4', 'avi', 'wmv']
RECORD_DELIM = ':::::'


def warnDuplicate(src, dst):
    print("Possible duplicate found: {}".format(src))
    print(" ^^^ {} already exists!!".format(dst))


def getCwd():
    return os.path.dirname(os.path.abspath(__file__))


def getMd5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        iChunk = 0
        for chunk in iter(lambda: f.read(4096), b""):
            if iChunk > N_MAX_CHUNKS:
                break
            hash_md5.update(chunk)
            iChunk += 1
    return hash_md5.hexdigest()


class RecordKeeper(object):
    def __init__(self, directory):
        self.encoding = 'utf-8'
        self.directory = directory
        self.dictionary = {}
        self.aFilename = []

    def loadRecord(self, filename='record.txt', encoding=None):
        if encoding is None:
            encoding = self.encoding
        recordPath = pjoin(self.directory, filename)
        try:
            with open(recordPath, 'r', encoding=encoding) as f:
                line = f.read()
        except Exception as e:
            print("Making a new record ...")
            with open(recordPath, 'w', encoding=encoding) as f:
                pass
            line = ''
        aRecord = line.split('\n')
        dictionary = self.dictionary
        for record in aRecord:
            if RECORD_DELIM in record:
                [hsh, fname] = record.split(RECORD_DELIM)
                dictionary[hsh] = fname
            else:
                if record != '':
                    print("Abnormal record found >> '{}'".format(record))
    
    def validateRecord(self):
        d = self.dictionary
        sRecord = set()
        aDuplicate = []
        for k,v in iter(d):
            if v in sRecord:
                aDuplicate.append(k)

    def saveRecord(self, filename='record.txt', encoding=None):
        if encoding is None:
            encoding = self.encoding
        recordPath = pjoin(self.directory, filename)
        with open(recordPath, 'w', encoding=encoding) as f:
            res = []
            for hsh in self.dictionary:
                fn = self.dictionary[hsh]
                output = '{}{}{}'.format(hsh, RECORD_DELIM, fn)
                res.append(output)
            res = '\n'.join(res)
            f.write(res)
            print('Saving record to {}'.format(recordPath))

    def getFilelist(self):
        aFilename = []
        for ft in ALLOWED_FILETYPES:
            aFilename += glob.glob1(directory, '*.{}'.format(ft))
        self.aFilename = aFilename
        return self.aFilename

    def record(self):
        aFilename = self.getFilelist()
        self.loadRecord()
        for fn in aFilename:
            src = pjoin(self.directory, fn)
            hsh = getMd5(src)
            if hsh not in self.dictionary:
                self.dictionary[hsh] = fn
        self.saveRecord()

    def restore(self):
        aFilename = self.getFilelist()
        self.loadRecord()
        aJob = []
        for fn in aFilename:
            src = pjoin(self.directory, fn)
            hsh = getMd5(src)
            if hsh in self.dictionary:
                newfn = self.dictionary[hsh]
                dst = pjoin(self.directory, newfn)
                if dst != src:
                    job = (src, dst)
                    aJob.append(job)

        for job in aJob:
            (src, dst) = job
            if os.path.exists(dst):
                warnDuplicate(src, dst)
            else:
                print("{}\n   ^^^ {}".format(dst, src))
                shutil.move(src, dst)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='The Record Keeper')
    parser.add_argument('command', type=str,
                        help='Available options: record or restore')
    parser.add_argument('-d', '--directory',
                        type=str, help='Directory location of the files')
    args = parser.parse_args()
    directory = getCwd() if args.directory is None else args.directory
    command = args.command
    rk = RecordKeeper(directory)
    if command.lower() == 'record':
        rk.record()
    elif command.lower() == 'restore':
        rk.restore()
    else:
        print('Unrecognized command {}'.format(command))
