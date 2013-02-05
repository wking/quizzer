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
import tempfile as _tempfile

from . import error as _error
from . import util as _util


LOG = _logging.getLogger(__name__)
QUESTION_CLASS = {}


def register_question(question_class):
    QUESTION_CLASS[question_class.__name__] = question_class


class Question (object):
    _state_attributes = [
        'id',
        'prompt',
        'answer',
        'multiline',
        'help',
        'dependencies',
        ]

    def __init__(self, **kwargs):
        self.__setstate__(kwargs)

    def __str__(self):
        return '<{} id:{!r}>'.format(type(self).__name__, self.id)

    def __repr__(self):
        return '<{} id:{!r} at {:#x}>'.format(
            type(self).__name__, self.id, id(self))

    def __getstate__(self):
        return {attr: getattr(self, attr)
                for attr in self._state_attributes} 

    def __setstate__(self, state):
        if 'id' not in state:
            state['id'] = state.get('prompt', None)
        if 'multiline' not in state:
            state['multiline'] = False
        if 'dependencies' not in state:
            state['dependencies'] = []
        for attr in self._state_attributes:
            if attr not in state:
                state[attr] = None
        self.__dict__.update(state)

    def check(self, answer):
        return answer == self.answer


class NormalizedStringQuestion (Question):
    def normalize(self, string):
        return string.strip().lower()

    def check(self, answer):
        return self.normalize(answer) == self.normalize(self.answer)


class ChoiceQuestion (Question):
    def check(self, answer):
        return answer in self.answer


class ScriptQuestion (Question):
    _state_attributes = Question._state_attributes + [
        'interpreter',
        'setup',
        'teardown',
        'timeout',
        ]

    def __setstate__(self, state):
        if 'interpreter' not in state:
            state['interpreter'] = 'sh'  # POSIX-compatible shell
        if 'timeout' not in state:
            state['timeout'] = 3
        for key in ['setup', 'teardown']:
            if key not in state:
                state[key] = []
        super(ScriptQuestion, self).__setstate__(state)

    def check(self, answer):
        # figure out the expected values
        e_status,e_stdout,e_stderr = self._invoke(self.answer)
        # get values for the user-supplied answer
        try:
            a_status,a_stdout,a_stderr = self._invoke(answer)
        except _error.CommandError as e:
            LOG.warning(e)
            return False
        for (name, e, a) in [
                ('stderr', e_stderr, a_stderr),
                ('status', e_status, a_status),
                ('stdout', e_stdout, a_stdout),
                ]:
            if a != e:
                if name == 'status':
                    LOG.info(
                        'missmatched {}, expected {!r} but got {!r}'.format(
                            name, e, a))
                else:
                    LOG.info('missmatched {}, expected:'.format(name))
                    LOG.info(e)
                    LOG.info('but got:')
                    LOG.info(a)
                return False
        return True

    def _invoke(self, answer):
        prefix = '{}-'.format(type(self).__name__)
        if not self.multiline:
            answer = [answer]
        with _tempfile.TemporaryDirectory(prefix=prefix) as tempdir:
            script = '\n'.join(self.setup + answer + self.teardown)
            status,stdout,stderr = _util.invoke(
                args=[self.interpreter],
                stdin=script,
                cwd=tempdir,
                universal_newlines=True,
                timeout=self.timeout,
                )
            dirname = _os_path.basename(tempdir)
        stdout = stdout.replace(dirname, '{}XXXXXX'.format(prefix))
        stderr = stderr.replace(dirname, '{}XXXXXX'.format(prefix))
        return status,stdout,stderr

for name,obj in list(locals().items()):
    if name.startswith('_'):
        continue
    try:
        subclass = issubclass(obj, Question)
    except TypeError:  # obj is not a class
        continue
    if subclass:
        register_question(obj)
del name, obj
