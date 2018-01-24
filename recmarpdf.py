#!/usr/bin/python

import os
import subprocess
import argparse
import sys


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

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--flat-out", nargs='?', type=str, default=None)
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    if args.flat_out and not os.path.exists(args.flat_out):
        print('generate directory {}'.format(args.flat_out))
        os.makedirs(args.flat_out)
    process_dir(args, ".")

if __name__ == '__main__':
  main()
