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