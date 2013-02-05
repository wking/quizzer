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
            q = _question.Question()
            q.__setstate__(state)
            self.append(q)

    def save(self, **kwargs):
        data = {
            'version': __version__,
            'questions': [question.__getstate__() for question in self],
            }
        with self._open(mode='w', **kwargs) as f:
            _json.dump(
                data, f, indent=2, separators=(',', ': '), sort_keys=True)
            f.write('\n')
