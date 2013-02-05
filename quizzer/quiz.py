import codecs as _codecs
import json as _json

from . import __version__
from . import question as _question


class Quiz (list):
    def __init__(self, questions=None, path=None, encoding=None):
        if questions is None:
            questions = []
        super(Quiz, self).__init__(questions)
        self.path = path
        self.encoding = encoding

    def _open(self, mode='r', path=None, encoding=None):
        if path:
            self.path = path
        if encoding:
            self.encoding = encoding
        return _codecs.open(self.path, mode, self.encoding)

    def load(self, **kwargs):
        with self._open(mode='r', **kwargs) as f:
            data = _json.load(f)
        version = data.get('version', None)
        if version != __version__:
            raise NotImplementedError('upgrade from {} to {}'.format(
                    version, __version__))
        for state in data['questions']:
            question_class_name = state.pop('class', 'Question')
            question_class = _question.QUESTION_CLASS[question_class_name]
            q = question_class()
            q.__setstate__(state)
            self.append(q)

    def save(self, **kwargs):
        questions = []
        for question in self:
            state = question.__getstate__()
            state['class'] = type(question).__name__
        data = {
            'version': __version__,
            'questions': questions,
            }
        with self._open(mode='w', **kwargs) as f:
            _json.dump(
                data, f, indent=2, separators=(',', ': '), sort_keys=True)
            f.write('\n')

    def leaf_questions(self):
        "Questions that are not dependencies of other question"
        dependents = set()
        for question in self:
            dependents.update(question.dependencies)
        return [q for q in self if q.id not in dependents]

    def get(self, id=None):
        matches = [q for q in self if q.id == id]
        if len(matches) == 1:
            return matches[0]
        elif len(matches) == 0:
            raise KeyError(id)
        raise NotImplementedError(
            'multiple questions with one ID: {}'.format(matches))
