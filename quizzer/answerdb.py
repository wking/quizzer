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
import datetime as _datetime
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
            try:
                upgrader = getattr(
                    self, '_upgrade_from_{}'.format(version.replace('.', '_')))
            except AttributeError as e:
                raise NotImplementedError('upgrade from {} to {}'.format(
                        version, __version__)) from e
            data = upgrader(data)
        self.update(data['answers'])
        if '' in self:
            self[None] = self.pop('')

    def save(self, **kwargs):
        answers = dict(self)
        if None in answers:
            answers[''] = answers.pop(None)
        data = {
            'version': __version__,
            'answers': answers,
            }
        with self._open(mode='w', **kwargs) as f:
            _json.dump(
                data, f, indent=2, separators=(',', ': '), sort_keys=True)
            f.write('\n')

    def add(self, question, answer, correct, user=None):
        if user == '':
            raise ValueError('the empty string is an invalid username')
        if user not in self:
            self[user] = {}
        if question.id not in self[user]:
            self[user][question.id] = []
        timezone = _datetime.timezone.utc
        timestamp = _datetime.datetime.now(tz=timezone).isoformat()
        self[user][question.id].append({
                'answer': answer,
                'correct': correct,
                'timestamp': timestamp,
                })

    def get_answers(self, user=None):
        if user == '':
            raise ValueError('the empty string is an invalid username')
        return self.get(user, {})

    def _get_questions(self, check, questions, user=None):
        if user == '':
            raise ValueError('the empty string is an invalid username')
        answers = self.get_answers(user=user)
        return [q for q in questions if check(question=q, answers=answers)]

    def get_answered(self, **kwargs):
        return self._get_questions(
            check=lambda question, answers: question.id in answers,
            **kwargs)

    def get_unanswered(self, **kwargs):
        return self._get_questions(
            check=lambda question, answers: question.id not in answers,
            **kwargs)

    def get_correctly_answered(self, **kwargs):
        return self._get_questions(
            check=lambda question, answers:
                True in [a['correct'] for a in answers.get(question.id, [])],
            **kwargs)

    def get_never_correctly_answered(self, **kwargs):
        return self._get_questions(
            check=lambda question, answers:
                True not in [a['correct']
                             for a in answers.get(question.id, [])],
            **kwargs)

    def _upgrade_from_0_1(self, data):
        data['version'] = __version__
        data['answers'] = {'': data['answers']}  # add user-id key
        return data

    _upgrade_from_0_2 = _upgrade_from_0_1
    _upgrade_from_0_3 = _upgrade_from_0_1
