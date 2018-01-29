#!/usr/bin/python

import os
import subprocess
import argparse
import sys
import json

class MetaInfo:

    def __init__(self, metafile=None):
        self.template = 'modern'
        if metafile:
            self.init_metafile(metafile)

    def parse_file(self, path):
        with open(path) as fd:
            return json.load(fd)

    def init_metafile(self, metafile):
        data = self.parse_file(metafile)
        if 'template' in data:
            if data['template'] == 'modern':
                self.template = 'modern'
            else:
                raise Exception('template not supported')



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

def meta_check(path, filename):
    metafile = '.{}.meta'.format(filename[0:-3])
    metapath = os.path.join(path, metafile)
    print(metapath)
    if not os.path.isfile(metapath):
        return MetaInfo()
    print('using meta file: {}'.format(metapath))
    return MetaInfo(metafile=metapath)

def execute(cmd):
    subprocess.call(cmd.split())

def pandoc_generator(md_in_path, pdf_out_path, meta):
    print(' generate PDF {}'.format(pdf_out_path))
    cmd = 'pandoc {} -o {}'.format(md_in_path, pdf_out_path)
    execute(cmd)

def process_document(args, path, filename):
    print('process {}'.format(os.path.join(path, filename)))
    if args.flat_out:
        pdf_out_path = os.path.join(args.flat_out, "{}.pdf".format(filename[0:-3]))
    else:
        pdf_out_path = os.path.join(path, "{}.pdf".format(filename[0:-3]))
    meta = meta_check(path, filename)
    md_in_path = sanity_file(path, filename)
    pandoc_generator(md_in_path, pdf_out_path, meta)
    os.remove(md_in_path)

def process_dir(args, path):
    for root, dirs, files in os.walk(path):
        path = root.split(os.sep)
        for filename in files:
            if not filename.endswith('.md'):
                continue
            process_document(args, root, filename)

def process_filelist(args, filelist):
    for filename in filelist:
        root = ''
        if not filename.endswith('.md'):
            print('no valid markdown file: {}, ignoring it'.format(filename))
            continue
        if not os.path.isfile(filename):
            print('no valid file: {}, ignoring it'.format(filename))
            continue
        filename = os.path.basename(filename)
        directory = os.path.dirname(filename)
        if not directory:
            directory = '.'
        process_document(args, directory, filename)


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
