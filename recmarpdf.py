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
import datetime

EXIT_SUCCESS = 0
EXIT_FAILURE = 1

ROOT_DIR = os.path.dirname(os.path.realpath(__file__))

class MetaInfo(object):

    class DocumentInfo(object):

        def __init__(self):
            self.title = None

        def feed(self, data):
            pass

    def __init__(self, metafile=None):
        self.cd_template()
        self.init_templates()
        self.default_template = 'modern'
        self.title = None
        if metafile:
            self.init_metafile(metafile)

    def cd_template(self):
        """
        it is required to cd into the template directory,
        if not we need to open the latex files in templates
        and modify path to images, etc. Which is cumbersome
        """
        template_dir = os.path.join(ROOT_DIR, 'templates')
        os.chdir(template_dir)

    def parse_file(self, path):
        with open(path) as fd:
            return json.load(fd)

    def template_path(self):
        if not self.template in self.templates:
            return self.templates[self.default_template]['path']
        return self.templates[self.template]['path']

    def init_templates(self):
        template_dir = os.path.join(ROOT_DIR, 'templates')
        self.templates = dict()
        for filename in os.listdir(template_dir):
            if not filename.endswith(".tex"):
                continue
            full_path = os.path.join(template_dir, filename)
            e = dict()
            e['path'] = full_path
            self.templates[filename[:-4]] = e
        print(self.templates)

    def init_metafile(self, metafile):
        data = self.parse_file(metafile)
        if 'template' in data:
            if data['template'] in ('modern'):
                self.template = 'modern'
            else:
                raise Exception('template not supported')
        if 'title' in data:
            self.title = data['title']


class MDObject(object):

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

def execute(cmd):
    subprocess.call(cmd, shell=True)


class Generator(object):

    def __init__(self):
        ret = EXIT_SUCCESS
        args = self.parse_args()
        if args.flat_out and not os.path.exists(args.flat_out):
            print('generate new directory {}'.format(args.flat_out))
            os.makedirs(args.flat_out)
        args.tmpdir = tempfile.mkdtemp()
        ret = self.process_stdin_list(args)
        shutil.rmtree(args.tmpdir)
        sys.exit(ret)

    def prepare_file(self, args, path, filename, meta):
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

    def meta_create(self, path, filename):
        metafile = '.{}.meta'.format(filename[0:-3])
        metapath = os.path.join(path, metafile)
        print(metapath)
        if not os.path.isfile(metapath):
            return MetaInfo()
        print('using meta file: {}'.format(metapath))
        return MetaInfo(metafile=metapath)

    def pandoc_generator(self, md_in_path, pdf_out_path, meta):
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
        options += '--template {} '.format(meta.template_path())

        #options += '-V documentclass=report '
        cmd = 'pandoc {} {} -o {}'.format(options, md_in_path, pdf_out_path)
        print(cmd)
        execute(cmd)

    def process_document(self, args, path, filename):
        print('process {}'.format(os.path.join(path, filename)))
        now = datetime.datetime.utcnow()
        date = '{:04d}-{:02d}-{:02d}'.format(now.year, now.month, now.day)
        new_doc_name = "{}-{}.pdf".format(date, filename[0:-3])
        if args.flat_out:
            pdf_out_path = os.path.join(args.flat_out, new_doc_name)
        else:
            pdf_out_path = os.path.join(path, new_doc_name)
        meta = self.meta_create(path, filename)
        md_in_path = self.prepare_file(args, path, filename, meta)
        self.pandoc_generator(md_in_path, pdf_out_path, meta)

    def process_dir(self, args, path):
        for root, dirs, files in os.walk(path):
            path = root.split(os.sep)
            for filename in files:
                if not filename.endswith('.md'):
                    continue
                self.process_document(args, root, filename)

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--flat-out", nargs='?', type=str, default=None)
        args = parser.parse_args()
        return args

    def process_stdin_list(self, args):
        try:
            filelist = json.load(sys.stdin)
        except Exception:
            print('json error in piped data, exit premature')
            return EXIT_FAILURE
        for fileentry in filelist:
            if not 'filename' in fileentry:
                print('not a valid entry in {}'.format(fileentry))
                continue
            path = fileentry['filename']
            root = ''
            if not path.endswith('.md'):
                print('no valid markdown file: {}, ignoring it'.format(path))
                continue
            if not path.startswith('/'):
                print('filepath must starts /: {}, ignoring it'.format(path))
                continue
            if not os.path.isfile(path):
                print('no valid file: {}, ignoring it'.format(path))
                continue
            filename = os.path.basename(path)
            directory = os.path.dirname(path)
            self.process_document(args, directory, filename)


if __name__ == '__main__':
    Generator()

