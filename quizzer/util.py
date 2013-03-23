# Copyright (C) 2013 W. Trevor King <wking@tremily.us>
#
# This file is part of quizzer.
#
# quizzer is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# quizzer is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# quizzer.  If not, see <http://www.gnu.org/licenses/>.

import logging as _logging
import os.path as _os_path
import subprocess as _subprocess
import sys as _sys
import tempfile as _tempfile

from . import error as _error


LOG = _logging.getLogger(__name__)


def invoke(args, stdin=None, stdout=_subprocess.PIPE, stderr=_subprocess.PIPE,
           universal_newlines=False, timeout=None, expect=None, **kwargs):
    if stdin:
        stdin_pipe = _subprocess.PIPE
    else:
        stdin_pipe = None
    try:
        p = _subprocess.Popen(
            args, stdin=stdin_pipe, stdout=stdout, stderr=stderr,
            universal_newlines=universal_newlines, **kwargs)
    except FileNotFoundError as e:
        raise _error.CommandError(arguments=args, stdin=stdin) from e
    if _sys.version_info >= (3, 3):  # Python >= 3.3
        try:
            stdout,stderr = p.communicate(input=stdin, timeout=timeout)
        except _subprocess.TimeoutExpired as e:
            p.kill()
            stdout,stderr = p.communicate()
            status = p.wait()
            raise _error.CommandError(
                msg='timeout ({}s) expired'.format(timeout),
                arguments=args, stdin=stdin, stdout=stdout, stderr=stderr,
                status=status) from e
    else:  # Python <= 3.2 don't support communicate(..., timeout)
        if timeout is not None:
            LOG.warning('Python version {} does not support timeouts'.format(
                    _sys.version.split()[0]))
        stdout,stderr = p.communicate(input=stdin)
    status = p.wait()
    if expect and status not in expect:
        raise _error.CommandError(
            msg='unexpected exit status ({} not in {})'.format(status, expect),
            args=args, stdin=stdin, stdout=stdout, stderr=stderr,
            status=status)
    return (status, stdout, stderr)

def invocation_difference(a_status, a_stdout, a_stderr,
                          b_status, b_stdout, b_stderr):
    for (name, a, b) in [
        ('stderr', a_stderr, b_stderr),
        ('status', a_status, b_status),
        ('stdout', a_stdout, b_stdout),
        ]:
        if a != b:
            return (name, a, b)

def format_invocation_difference(name, a, b):
    if name == 'status':
        return 'missmatched {}, expected {!r} but got {!r}'.format(name, a, b)
    else:
        return '\n'.join([
                'missmatched {}, expected:'.format(name),
                a,
                'but got:',
                b,
                ])


class TemporaryDirectory (object):
    """A temporary directory for testing answers

    >>> t = TemporaryDirectory()

    Basic command execution:

    >>> t.invoke('/bin/sh', 'touch a b c')
    (0, '', '')
    >>> t.invoke('/bin/sh', 'ls')
    (0, 'a\nb\nc\n', '')

    Captured stdout and stderr have instances of the random temporary
    directory name normalized for easy comparison:

    >>> t.invoke('/bin/sh', 'pwd')
    (0, '/tmp/TemporaryDirectory-XXXXXX\n', '')

    >>> t.cleanup()
    """
    def __init__(self):
        self.prefix = '{}-'.format(type(self).__name__)
        self.tempdir = _tempfile.TemporaryDirectory(prefix=self.prefix)

    def cleanup(self):
        if self.tempdir:
            self.tempdir.cleanup()
            self.tempdir = None

    def __del__(self):
        self.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.cleanup()

    def invoke(self, interpreter, text, universal_newlines=True, **kwargs):
        if not self.tempdir:
            raise RuntimeError(
                'cannot invoke() on a cleaned up {}'.format(
                    type(self).__name__))
        with _tempfile.NamedTemporaryFile(
                mode='w', prefix='{}script-'.format(self.prefix)
                ) as tempscript:
            tempscript.write(text)
            tempscript.flush()
            status,stdout,stderr = invoke(
                args=[interpreter, tempscript.name],
                cwd=self.tempdir.name,
                universal_newlines=universal_newlines,
                **kwargs)
            dirname = _os_path.basename(self.tempdir.name)
        if stdout:
            stdout = stdout.replace(dirname, '{}XXXXXX'.format(self.prefix))
        if stderr:
            stderr = stderr.replace(dirname, '{}XXXXXX'.format(self.prefix))
        return (status, stdout, stderr)
