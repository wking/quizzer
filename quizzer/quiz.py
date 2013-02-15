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

import codecs as _codecs
import json as _json

from . import __version__
from . import question as _question


class Quiz (list):
    def __init__(self, questions=None, path=None, encoding=None,
                 copyright=None, introduction=None):
        if questions is None:
            questions = []
        super(Quiz, self).__init__(questions)
        self.path = path
        self.encoding = encoding
        self.copyright = copyright
        self.introduction = introduction

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
        self.copyright = data.get('copyright', None)
        self.introduction = data.get('introduction', None)
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
            'copyright': self.copyright,
            'introduction': self.introduction,
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
