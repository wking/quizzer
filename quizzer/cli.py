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

import argparse as _argparse
import locale as _locale

from . import __doc__ as _module_doc
from . import __version__
from . import answerdb as _answerdb
from . import quiz as _quiz
from .ui import cli as _cli


def main():
    encoding = _locale.getpreferredencoding(do_setlocale=True)

    parser = _argparse.ArgumentParser(description=_module_doc)
    parser.add_argument(
        '--version', action='version',
        version='%(prog)s {}'.format(__version__))
    parser.add_argument(
        '-a', '--answers', metavar='ANSWERS', default='answers.json',
        help='path to an answers database')
    parser.add_argument(
        'quiz', metavar='QUIZ',
        help='path to a quiz file')

    args = parser.parse_args()

    quiz = _quiz.Quiz(path=args.quiz, encoding=encoding)
    quiz.load()
    answers = _answerdb.AnswerDatabase(path=args.answers, encoding=encoding)
    try:
        answers.load()
    except IOError:
        pass
    ui = _cli.CommandLineInterface(quiz=quiz, answers=answers)
    ui.run()
    ui.answers.save()
    ui.display_results()
