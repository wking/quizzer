import argparse as _argparse

from . import __doc__ as _module_doc
from . import __version__
from . import quiz as _quiz


def main():
    parser = _argparse.ArgumentParser(description=_module_doc)
    parser.add_argument(
        '--version', action='version',
        version='%(prog)s {}'.format(__version__))
    parser.add_argument(
        'quiz', metavar='QUIZ',
        help='path to a quiz file')

    args = parser.parse_args()

    quiz = Quiz()
    quiz.load(args.quiz)
    for question in quiz:
        print(question)
