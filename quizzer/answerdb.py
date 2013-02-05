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


class AnswerDatabase (dict):
    def __init__(self, path=None, encoding=None):
        super(AnswerDatabase, self).__init__()
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
        self.update(data['answers'])

    def save(self, **kwargs):
        data = {
            'version': __version__,
            'answers': self,
            }
        with self._open(mode='w', **kwargs) as f:
            _json.dump(
                data, f, indent=2, separators=(',', ': '), sort_keys=True)
            f.write('\n')

    def add(self, question, answer, correct):
        if question.id not in self:
            self[question.id] = []
        self[question.id].append({
                'answer': answer,
                'correct': correct,
                })

    def get_answered(self, questions):
        return [q for q in questions if q.id in self]

    def get_unanswered(self, questions):
        return [q for q in questions if q.id not in self]

    def get_correctly_answered(self, questions):
        return [q for q in questions
                if True in [a['correct'] for a in self.get(q.id, [])]]

    def get_never_correctly_answered(self, questions):
        return [q for q in questions
                if True not in [a['correct'] for a in self.get(q.id, [])]]
