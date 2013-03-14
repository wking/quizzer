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
import os as _os

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
        'accept_all',
        'multiline',
        'help',
        'dependencies',
        'tags',
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
        if 'dependencies' not in state:
            state['dependencies'] = []
        if 'tags' not in state:
            state['tags'] = set()
        else:
            state['tags'] = set(state['tags'])
        for attr in ['accept_all', 'multiline']:
            if attr not in state:
                state[attr] = False
        for attr in self._state_attributes:
            if attr not in state:
                state[attr] = None
        self.__dict__.update(state)

    def check(self, answer):
        if self.accept_all:
            return (True, None)
        return self._check(answer)

    def _check(self, answer):
        correct = answer == self.answer
        details = None
        if not correct:
            details = 'answer ({}) does not match expected value'.format(
                answer)
        return (correct, details)

    def _format_attribute(self, attribute, newline='\n'):
        value = getattr(self, attribute)
        if isinstance(value, str):
            return value
        return newline.join(value)

    def format_prompt(self, **kwargs):
        return self._format_attribute(attribute='prompt', **kwargs)

    def format_help(self, **kwargs):
        return self._format_attribute(attribute='help', **kwargs)


class NormalizedStringQuestion (Question):
    def normalize(self, string):
        return string.strip().lower()

    def _check(self, answer):
        normalized_answer = self.normalize(answer)
        correct = normalized_answer == self.normalize(self.answer)
        details = None
        if not correct:
            details = ('normalized answer ({}) does not match expected value'
                       ).format(normalized_answer)
        return (correct, details)


class ChoiceQuestion (Question):
    _state_attributes = Question._state_attributes + [
        'display_choices',
        ]

    def __setstate__(self, state):
        for key in ['display_choices']:
            if key not in state:
                state[key] = False
        super(ChoiceQuestion, self).__setstate__(state)

    def _check(self, answer):
        correct = answer in self.answer
        details = None
        if not correct:
            details = 'answer ({}) is not in list of expected values'.format(
                answer)
        return (correct, details)


class ScriptQuestion (Question):
    """Question testing scripting knowledge

    Or using a script interpreter (like the POSIX shell) to test some
    other knowledge.

    If stdout/stderr capture is acceptable (e.g. if you're only
    running non-interactive commands or curses applications that grab
    the TTY directly), you can just run `.check()` like a normal
    question.

    If, on the other hand, you want users to be able to interact with
    stdout and stderr (e.g. to drop into a shell in the temporary
    directory), use:

        tempdir = q.setup_tempdir()
        try:
            tempdir.invoke(..., env=q.get_environment())
            # can call .invoke() multiple times here
            self.check(tempdir=tempdir)  # optional answer argument
        finally:
            tempdir.cleanup()  # occasionally redundant, but that's ok
    """
    _state_attributes = Question._state_attributes + [
        'interpreter',
        'setup',
        'pre_answer',
        'post_answer',
        'teardown',
        'environment',
        'allow_interactive',
        'compare_answers',
        'timeout',
        ]

    def __setstate__(self, state):
        if 'interpreter' not in state:
            state['interpreter'] = 'sh'  # POSIX-compatible shell
        if 'timeout' not in state:
            state['timeout'] = 3
        if 'environment' not in state:
            state['environment'] = {}
        for key in ['allow_interactive', 'compare_answers']:
            if key not in state:
                state[key] = False
        for key in ['setup', 'pre_answer', 'post_answer', 'teardown']:
            if key not in state:
                state[key] = []
        super(ScriptQuestion, self).__setstate__(state)

    def run(self, tempdir, lines, **kwargs):
        text = '\n'.join(lines + [''])
        try:
            status,stdout,stderr = tempdir.invoke(
                interpreter=self.interpreter, text=text,
                timeout=self.timeout, **kwargs)
        except:
            tempdir.cleanup()
            raise
        else:
            return (status, stdout, stderr)

    def setup_tempdir(self):
        tempdir = _util.TemporaryDirectory()
        self.run(tempdir=tempdir, lines=self.setup)
        return tempdir

    def teardown_tempdir(self, tempdir):
        return self.run(tempdir=tempdir, lines=self.teardown)

    def get_environment(self):
        if self.environment:
            env = {}
            env.update(_os.environ)
            env.update(self.environment)
            return env

    def _invoke(self, answer=None, tempdir=None):
        """Run the setup/answer/teardown process

        If tempdir is not None, skip the setup process.
        If answer is None, skip the answer process.

        In any case, cleanup the tempdir before returning.
        """
        if not tempdir:
            tempdir = self.setup_tempdir()
        try:
            if answer:
                if not self.multiline:
                    answer = [answer]
                a_status,a_stdout,a_stderr = self.run(
                    tempdir=tempdir,
                    lines=self.pre_answer + answer + self.post_answer,
                    env=self.get_environment())
            else:
                a_status = a_stdout = a_stderr = None
            t_status,t_stdout,t_stderr = self.teardown_tempdir(tempdir=tempdir)
        finally:
            tempdir.cleanup()
        return (a_status,a_stdout,a_stderr,
                t_status,t_stdout,t_stderr)

    def _check(self, answer=None, tempdir=None):
        """Compare the user's answer with expected values

        Arguments are passed through to ._invoke() for calculating the
        user's response.
        """
        details = None
        # figure out the expected values
        (ea_status,ea_stdout,ea_stderr,
         et_status,et_stdout,et_stderr) = self._invoke(answer=self.answer)
        # get values for the user-supplied answer
        try:
            (ua_status,ua_stdout,ua_stderr,
             ut_status,ut_stdout,ut_stderr) = self._invoke(
                answer=answer, tempdir=tempdir)
        except (KeyboardInterrupt, _error.CommandError) as e:
            if isinstance(e, KeyboardInterrupt):
                details = 'KeyboardInterrupt'
            else:
                details = str(e)
            return (False, details)
        # compare user-generated output with expected values
        if answer:
            if self.compare_answers:
                difference = _util.invocation_difference(  # compare answers
                    ea_status, ea_stdout, ea_stderr,
                    ua_status, ua_stdout, ua_stderr)
                if difference:
                    details = _util.format_invocation_difference(*difference)
                    return (False, details)
            elif ua_stderr:
                LOG.warning(ua_stderr)
        difference = _util.invocation_difference(  # compare teardown
            et_status, et_stdout, et_stderr,
            ut_status, ut_stdout, ut_stderr)
        if difference:
            details = _util.format_invocation_difference(*difference)
            return (False, details)
        return (True, None)


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
