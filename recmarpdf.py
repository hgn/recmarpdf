#!/usr/bin/python

import os
import subprocess
import argparse
import sys

class MetaInfo:

    def __init__(self):
        self.template = 'modern'



def sanity_file(path, filename):
    full = os.path.join(path, filename)
    content_new = ""
    with open(full, 'r') as fd:
        for line in fd:
            content_new += line

    newname = "{}-pandoc-modified-tmp.md".format(filename[0:-3])
    full_new = os.path.join(path, newname)

    fd = open(full_new, "w")
    fd.write(content_new)
    fd.close()
    return full_new

def execute(cmd):
    subprocess.call(cmd.split())

def process_document(args, path, filename):
    print('process {}'.format(os.path.join(path, filename)))
    if args.flat_out:
        pdf_out_path = os.path.join(args.flat_out, "{}.pdf".format(filename[0:-3]))
    else:
        pdf_out_path = os.path.join(path, "{}.pdf".format(filename[0:-3]))
    new = sanity_file(path, filename)
    print(' generate PDF {}'.format(pdf_out_path))
    cmd = 'pandoc {} -o {}'.format(new, pdf_out_path)
    execute(cmd)
    os.remove(new)

def process_dir(args, path):
    for root, dirs, files in os.walk(path):
        path = root.split(os.sep)
        for filename in files:
            if not filename.endswith('.md'):
                continue
            process_document(args, root, filename)

def process_filelist(args, filelist):
    for filename in filelist:
        # if absolut pathname? If not add relative pathname
        # to filename
        # check if file exists, if not ignore it, warn user
        pass

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--flat-out", nargs='?', type=str, default=None)
    parser.add_argument("--documents", nargs='?', type=str, default=None)
    args = parser.parse_args()
    if args.documents:
        args.documents = filter(None, args.documents.split(','))
    return args

def main():
    args = parse_args()
    if args.flat_out and not os.path.exists(args.flat_out):
        print('generate directory {}'.format(args.flat_out))
        os.makedirs(args.flat_out)
    if not args.documents:
        process_dir(args, ".")
    else:
        process_filelist(args, args.documents)

if __name__ == '__main__':
  main()
