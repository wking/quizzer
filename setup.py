"Break learning up into small task-based tests for focused study."

import codecs as _codecs
from distutils.core import setup as _setup
import os.path as _os_path

from quizzer import __version__


_this_dir = _os_path.dirname(__file__)

_setup(
    name='quizzer',
    version=__version__,
    maintainer='W. Trevor King',
    maintainer_email='wking@tremily.us',
    url='http://blog.tremily.us/posts/quizzer/',
    download_url='http://git.tremily.us/?p=quizzer.git;a=snapshot;h=v{};sf=tgz'.format(__version__),
    license = 'GNU General Public License (GPL)',
    platforms = ['all'],
    description = __doc__,
    long_description=_codecs.open(
        _os_path.join(_this_dir, 'README'), 'r', 'utf-8').read(),
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Education',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Topic :: Education',
        'Topic :: Education :: Computer Aided Instruction (CAI)',
        ],
    scripts = ['pq.py'],
    packages = ['quizzer', 'quizzer.ui'],
    provides = ['quizzer', 'quizzer.ui'],
    )
