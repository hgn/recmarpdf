#!/usr/bin/python

import os
import subprocess


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

def process_document(path, filename):
    print('process {}'.format(os.path.join(path, filename)))
    pdf_out_path = os.path.join(path, "{}.pdf".format(filename[0:-3]))
    new = sanity_file(path, filename)
    print(' generate PDF {}'.format(pdf_out_path))
    cmd = 'pandoc {} -o {}'.format(new, pdf_out_path)
    execute(cmd)
    os.remove(new)

def process_dir(path):
    for root, dirs, files in os.walk(path):
        path = root.split(os.sep)
        for filename in files:
            if not filename.endswith('.md'):
                continue
            process_document(root, filename)

def main():
    process_dir(".")

if __name__ == '__main__':
  main()
