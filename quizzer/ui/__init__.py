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

import importlib as _importlib

from .. import answerdb as _answerdb


INTERFACES = ['cli']


class UserInterface (object):
    "Give a quiz over a generic user interface"
    def __init__(self, quiz=None, answers=None, stack=None):
        self.quiz = quiz
        if answers is None:
            answers = _answerdb.AnswerDatabase()
        self.answers = answers
        if stack is None:
            stack = self.answers.get_never_correctly_answered(
                questions=quiz.leaf_questions())
        self.stack = stack

    def run(self):
        raise NotImplementedError()

    def get_question(self):
        if self.stack:
            return self.stack.pop(0)

    def process_answer(self, question, answer, **kwargs):
        correct,details = question.check(answer=answer, **kwargs)
        self.answers.add(question=question, answer=answer, correct=correct)
        if not correct:
            self.stack.insert(0, question)
            for qid in reversed(question.dependencies):
                self.stack.insert(0, self.quiz.get(id=qid))
        return (correct, details)


def get_ui(name):
    """Get the UserInterface subclass from a UI submodule

    >>> get_ui('cli')
    <class 'quizzer.ui.cli.CommandLineInterface'>
    """
    module = _importlib.import_module('{}.{}'.format(__name__, name))
    for name in dir(module):
        obj = getattr(module, name)
        try:
            subclass = issubclass(obj, UserInterface)
        except TypeError as e:  # obj is not a class
            continue
        if subclass:
            return obj
    raise ValueError(name)
