#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class Urgency:

    CRITICAL = 'critical'
    NORMAL = 'normal'
    LOW = 'low'

def proc(args):
    import subprocess
    res = subprocess.run(args, capture_output=True)
    if res.returncode != 0:
        raise RuntimeError('Failed to run command with error: {}'.format(res.stderr.decode('utf-8')))

    ret = res.stdout.decode('utf-8')
    if ret:
        return ret[:-1] if ret[-1] == '\n' else ret
    else:
        return ''

def send_message(title, message, urgency=Urgency.NORMAL, duration_ms=3000):
    proc(['notify-send', '-u', urgency, '-t', str(duration_ms), title, message])

def gen_license():
    import datetime
    name = proc(['git', 'config', 'user.name'])
    email = proc(['git', 'config', 'user.email'])
    date = datetime.date.today().year
    ret = """// Copyright © {0} {1}
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the “Software”), to
// deal in the Software without restriction, including without limitation the
// rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
// sell copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
// FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
// IN THE SOFTWARE.
//
//     Author(s):
//     - {1} ({2})
""".format(date, name, email)
    return ret

def gen_header(namespace=None, class_=None, license=None):
    ret = ''
    body = ''

    # if there's a license, add it
    if license:
        ret = license

    ret = '{}{}#pragma once\n'.format(ret, '\n' if ret else '')

    # if there's a class, generate it
    if class_:
        body = '''class {}
{{
public:

}};'''.format(class_)

    # if there's a namespace, use it to generate final output
    if namespace:
        ret = ret + '\n' + '''namespace {}
{{
{}
}}'''.format(namespace, body)
    # otherwise just add the body to the license
    else:
        ret = ret + '\n' + body
    return ret

def gen_cpp(namespace=None, class_=None, file_=None, license=None):
    ret = ''
    body = ''

    # if there's a license, add it
    if license:
        ret = license

    if file_:
        ret = ret + ('\n' if ret else '') + '#include "{0}.h"\n'.format(file_)

    # if there's a namespace, use it to generate final output
    if namespace:
        ret = ret + '\n' + 'namespace {}\n{{\n}}'.format(namespace)

    return ret

def resolve_cmakelists(directory, filename, header_only):
    import re
    lines = []
    insert_point = None
    print('Found a CMakeLists.txt file')
    a = input('Attempt to add files to CMakeLists.txt? [Y/N]: ')
    if a not in 'yY':
        return

    with open('CMakeLists.txt') as f:
        lines = f.readlines()

    def add_block(lines, pattern, type_, file_ext):
        start = -1
        for i, l in enumerate(lines):
            if start > 0:
                m = re.search('\)', l)
                if m:
                    end = i
                    break
            else:
                m = re.search('(?<=set\()\w*' + pattern + '\w*', l)
                if m:
                    print('Got a match: {}'.format(m.group(0)))
                    if input('Add {} to this block?: [Y/N]: '.format(type_)) in 'yY':
                        start = i

        l2 = list(set(lines[start+1:end] + ['    {}/{}.{}\n'.format(directory, filename, file_ext)]))
        l2.sort()
        ret = lines[:start+1] + l2 + lines[end:]
        return ret

    if not header_only:
        lines = add_block(lines, 'SRC', 'source', 'cpp')
    lines = add_block(lines, 'HEADER', 'header', 'h')

    with open('CMakeLists.txt', 'w') as f:
        f.writelines(lines)

    print('Updated CMakeLists.txt')


def main(args):
    import argparse
    import os

    parser = argparse.ArgumentParser()
    parser.add_argument('--header', action='store_true', help='Creates only a header')
    parser.add_argument('-c', '--class', dest='class_', help='ClassName')
    parser.add_argument('-n', '--namespace' , help='Name of namespace to use')
    parser.add_argument('--file-name', '--fn' , help='Base for the filename (foobar -> foobar.{h,cpp})')
    parser.add_argument('-o', '--output' , help='Directory in which to create the file(s)')
    args = parser.parse_args()

    license = gen_license()

    path = args.output
    if path is None or not os.path.isdir(path):
        raise RuntimeError('The given path doesn\'t exist! ({})'.format(path))

    path = path[:-1] if path[-1] == '/' else path

    if not args.file_name:
        raise RuntimeError('No file-name given')

    h = gen_header(namespace=args.namespace, class_=args.class_, license=license)
    with open('{}/{}.h'.format(path, args.file_name), 'w') as f:
        f.write(h)

    if not args.header:
        c = gen_cpp(namespace=args.namespace, class_=args.class_, license=license, file_=args.file_name)
        with open('{}/{}.cpp'.format(path, args.file_name), 'w') as f:
            f.write(c)

    if os.path.exists('CMakeLists.txt'):
        resolve_cmakelists(path, args.file_name, args.header)

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv[1:]))
