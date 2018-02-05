#!/usr/bin/python3

import os
import subprocess
import argparse
import sys
import json
import tempfile
import shutil
import re
import pathlib

class MetaInfo:

    def __init__(self, metafile=None):
        self.template = 'modern'
        self.title = None
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
        if 'title' in data:
            self.title = data['title']


class MDObject:

    def __init__(self, path):
        self.path = path
        self.title = 'unknown'
        self.lines = []
        self._has_only_one_h1 = None
        self.read()

    def has_exactly_one_h1(self):
        return self._has_only_one_h1 == True

    def _check_has_only_one_h1(self, line):
        if not line.startswith('#'):
            return
        words = line.split()
        if len(words[0]) == 1:
            if self._has_only_one_h1 == None:
                self.title = ' '.join(words[1:])
                self._has_only_one_h1 = True
            else:
                self._has_only_one_h1 = False
                self.title = 'unknown'

    def read(self):
        content_new = ""
        with open(self.path, 'r') as fd:
            for line in fd:
                self._check_has_only_one_h1(line)
                self.lines.append(line)

    def unident(self):
        '''h2 -> h1, h3 -> h2, ... '''
        lines_updates = []
        for line in self.lines:
            if not line.startswith('#'):
                lines_updates.append(line)
                continue
            words = line.split()
            if len(words[0]) == 1:
                # remove title, ignore line, but check that
                # title is already specified
                assert(self.title != 'unknown')
                continue
            elif len(words[0]) > 1:
                words[0] = words[0][0:len(words[0]) - 1]
                lines_updates.append(" ".join(words))
        # seems legit, now update all lines
        self.lines = lines_updates

    def _as_str(self):
        s = ''
        for line in self.lines:
            s += line
        return s

    def save_modified(self, path):
        fd = open(path, "w")
        fd.write(self._as_str())
        fd.close()

    def set_clone_path(self, path):
        self.clone_path = path

    def set_md_path(self, path):
        self.md_path = path

    def copy_clone_files(self):
        for i, line in enumerate(self.lines):
            regex = '!\[(.*)\]\((.*)\)'
            m = re.search(regex, line)
            if not m:
                continue
            alt = m.group(1)
            img = m.group(2)
            if img[-3:] not in ('gif', 'png', 'svg', 'pdf', 'jpg') and img[-4:] != 'jpeg':
                continue
            full = os.path.join(self.md_path, img)
            clone_full = pathlib.Path(self.clone_path, full)
            os.makedirs(os.path.dirname(clone_full), exist_ok=True)
            if img[-3:] != 'svg':
                if not os.path.isfile(full):
                    raise
                shutil.copyfile(full, clone_path)
                self.lines[i] = '![{}]({})'.format(alt, clone_full)
            else: # SVG
                clone_path = pathlib.Path(str(clone_full)[:-3] + 'pdf')
                self.svg_to_pdf(full, clone_path)
                self.lines[i] = '![{}]({})\n'.format(alt, clone_path)
            print(clone_full)

    def svg_to_pdf(self, svg_in, pdf_out):
        cmd = 'inkscape {} -A {}'.format(svg_in, pdf_out)
        execute(cmd)




def prepare_file(args, path, filename, meta):
    full = os.path.join(path, filename)
    md_object = MDObject(full)
    if md_object.has_exactly_one_h1():
        md_object.unident()
        if not meta.title:
            # if meta data has set a title this has precedence
            # over h1 titles in files
            meta.title = md_object.title
    else:
        # ok, several h1, seems like a normal document
        # with several h1 headings
        # do nothing for now
        pass
    newname = "{}-pandoc-modified-tmp.md".format(filename[0:-3])
    full_new = os.path.join(args.tmpdir, path, newname)
    os.makedirs(os.path.join(args.tmpdir, path), exist_ok=True)
    md_object.set_clone_path(args.tmpdir)
    md_object.set_md_path(path)
    md_object.copy_clone_files()
    md_object.save_modified(full_new)
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
    subprocess.call(cmd, shell=True)

def pandoc_generator(md_in_path, pdf_out_path, meta):
    print(' generate PDF {}'.format(pdf_out_path))
    options = ''
    options += '--toc '
    #options += '--toc-depth=6 '
    #options += '--base-header-level=1 '
    options += '--standalone '
    if meta.title:
        options += '-V title=\'{}\' '.format(meta.title)
    #options += '--toc '
    options += '--latex-engine=xelatex '
    options += '--template template-one.tex '

    #options += '-V documentclass=report '
    cmd = 'pandoc {} {} -o {}'.format(options, md_in_path, pdf_out_path)
    print(cmd)
    execute(cmd)

def process_document(args, path, filename):
    print('process {}'.format(os.path.join(path, filename)))
    if args.flat_out:
        pdf_out_path = os.path.join(args.flat_out, "{}.pdf".format(filename[0:-3]))
    else:
        pdf_out_path = os.path.join(path, "{}.pdf".format(filename[0:-3]))
    meta = meta_check(path, filename)
    md_in_path = prepare_file(args, path, filename, meta)
    pandoc_generator(md_in_path, pdf_out_path, meta)

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
    args.tmpdir = tempfile.mkdtemp()
    if not args.documents:
        process_dir(args, ".")
    else:
        process_filelist(args, args.documents)
    #shutil.rmtree(args.tmpdir)

if __name__ == '__main__':
  main()
