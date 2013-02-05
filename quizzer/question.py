import logging as _logging
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
        with _tempfile.TemporaryDirectory(
                prefix='{}-'.format(type(self).__name__),
                ) as tempdir:
            script = '\n'.join(self.setup + [answer] + self.teardown)
            return _util.invoke(
                args=[self.interpreter],
                stdin=script,
                cwd=tempdir,
                universal_newlines=True,
                timeout=self.timeout,)

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
