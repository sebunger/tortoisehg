#!/usr/bin/env python
"""Run a set of tests by Mercurial's test runner

Usage::

    % HGPATH=path/to/mercurial ./run-hgtests.py
"""

import os, shutil, subprocess, sys

def run(args):
    testdir = os.path.dirname(__file__)
    hgpath = os.path.abspath(os.environ.get('HGPATH', ''))
    thgpath = os.path.abspath(
        os.environ.get('THGPATH', os.path.join(testdir, '..')))

    # as of Mercurial 3.1, TTest expects "hghave" executable in testdir
    shutil.copy(os.path.join(hgpath, 'tests', 'hghave'), testdir)

    fullargs = [sys.executable, os.path.join(hgpath, 'tests', 'run-tests.py')]
    fullargs.extend(args)
    env = os.environ.copy()
    env['HGPATH'] = hgpath  # absolute path that can be referenced by tests
    env['PYTHONPATH'] = thgpath + os.pathsep + env.get('PYTHONPATH', '')
    return subprocess.call(fullargs, cwd=testdir, env=env)

if __name__ == '__main__':
    sys.exit(run(sys.argv[1:]))
