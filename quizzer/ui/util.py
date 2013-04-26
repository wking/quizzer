# Copyright

"""View files using mailcap-specified commands
"""

import logging as _logging
import mailcap as _mailcap
import mimetypes as _mimetypes
import shlex as _shlex
if not hasattr(_shlex, 'quote'):  # Python < 3.3
    import pipes as _pipes
    _shlex.quote = _pipes.quote
import subprocess as _subprocess


_LOG = _logging.getLogger(__name__)
_CAPS = _mailcap.getcaps()


def mailcap_view(path, content_type=None, background=False):
    if content_type is None:
        content_type,encoding = _mimetypes.guess_type(path)
        if content_type is None:
            return 1
        _LOG.debug('guessed {} for {}'.format(content_type, path))
    match = _mailcap.findmatch(
        _CAPS, content_type, filename=_shlex.quote(path))
    if match[0] is None:
        _LOG.warn('no mailcap viewer found for {}'.format(content_type))
        raise NotImplementedError(content_type)
    _LOG.debug('view {} with: {}'.format(path, match[0]))
    process = _subprocess.Popen(match[0], shell=True)
    if background:
        return process
    return process.wait()
