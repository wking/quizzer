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

import subprocess as _subprocess

from . import error as _error


def invoke(args, stdin=None, universal_newlines=False, timeout=None,
           expect=None, **kwargs):
    if stdin:
        stdin_pipe = _subprocess.PIPE
    else:
        stdin_pipe = None
    try:
        p = _subprocess.Popen(
            args, stdin=stdin_pipe, stdout=_subprocess.PIPE,
            stderr=_subprocess.PIPE, universal_newlines=universal_newlines,
            **kwargs)
    except FileNotFoundError as e:
        raise _error.CommandError(arguments=args, stdin=stdin) from e
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
    status = p.wait()
    if expect and status not in expect:
        raise _error.CommandError(
            msg='unexpected exit status ({} not in {})'.format(status, expect),
            args=args, stdin=stdin, stdout=stdout, stderr=stderr,
            status=status)
    return (status, stdout, stderr)
