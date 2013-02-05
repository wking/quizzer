# Copyright

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
