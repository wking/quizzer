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

import cmd as _cmd
try:
    import readline as _readline
except ImportError as _readline_import_error:
    _readline = None

try:
    from pygments.console import colorize as _colorize
except ImportError as e:
    def _colorize(color_key=None, text=None):
        return text
    print(e)

from . import UserInterface


class QuestionCommandLine (_cmd.Cmd):
    _help = [
        'Type help or ? to list commands.',
        'Non-commands will be interpreted as answers.',
        'Use a blank line to terminate multi-line answers.',
        ]
    intro = '\n'.join(['Welcome to the quizzer shell.'] + _help)
    _prompt = 'quizzer? '

    def __init__(self, ui):
        super(QuestionCommandLine, self).__init__()
        self.ui = ui

    def preloop(self):
        self.question = self.ui.get_question()
        self._reset()

    def _reset(self):
        self.answers = []
        self._set_ps1()

    def _set_ps1(self):
        "Pose a question and prompt"
        if self.question:
            self.prompt = '\n{}\n{}'.format(
                _colorize(
                    self.ui.colors['question'], self.question.format_prompt()),
                _colorize(self.ui.colors['prompt'], self._prompt))
        else:
            self.prompt = _colorize(self.ui.colors['prompt'], self._prompt)

    def _set_ps2(self):
        "Just prompt (without the question, e.g. for multi-line answers)"
        self.prompt = _colorize(self.ui.colors['prompt'], self._prompt)

    def default(self, line):
        self.answers.append(line)
        if self.question.multiline:
            self._set_ps2()
        else:
            return self._answer()

    def emptyline(self):
        return self._answer()

    def _answer(self):
        if self.question.multiline:
            answer = self.answers
        elif self.answers:
            answer = self.answers[0]
        else:
            answer = ''
        correct = self.ui.process_answer(question=self.question, answer=answer)
        if correct:
            print(_colorize(self.ui.colors['correct'], 'correct\n'))
        else:
            print(_colorize(self.ui.colors['incorrect'], 'incorrect\n'))
        self.question = self.ui.get_question()
        if not self.question:
            return True  # out of questions
        self._reset()

    def do_answer(self, arg):
        """Explicitly add a line to your answer

        This is useful if the line you'd like to add starts with a
        quizzer-shell command.  For example:

          quizzer? answer help=5
        """
        return self.default(arg)

    def do_quit(self, arg):
        "Stop taking the quiz"
        self._reset()
        return True

    def do_hint(self, arg):
        "Show a hint for the current question"
        self._reset()
        print(self.question.format_help())

    def do_help(self, arg):
        'List available commands with "help" or detailed help with "help cmd"'
        if not arg:
            print('\n'.join(self._help))
        super(QuestionCommandLine, self).do_help(arg)


class CommandLineInterface (UserInterface):
    colors = {  # listed in pygments.console.light_colors
        'question': 'turquoise',
        'prompt': 'blue',
        'correct': 'green',
        'incorrect': 'red',
        'result': 'fuchsia',
        }

    def run(self):
        if not self.stack:
            return
        cmd = QuestionCommandLine(ui=self)
        cmd.cmdloop()
        print()

    def display_results(self):
        print(_colorize(self.colors['result'], 'results:'))
        for question in self.quiz:
            if question.id in self.answers:
                self.display_result(question=question)
                print()
        self.display_totals()

    def display_result(self, question):
        answers = self.answers.get(question.id, [])
        print('question:')
        print('  {}'.format(
            _colorize(
                self.colors['question'],
                question.format_prompt(newline='\n  '))))
        la = len(answers)
        lc = len([a for a in answers if a['correct']])
        print('answers: {}/{} ({:.2f})'.format(lc, la, float(lc)/la))
        for answer in answers:
            if answer['correct']:
                correct = 'correct'
            else:
                correct = 'incorrect'
            correct = _colorize(self.colors[correct], correct)
            ans = answer['answer']
            if question.multiline:
                ans = '\n                '.join(ans)
            print('  you answered: {}'.format(ans))
            print('     which was: {}'.format(correct))

    def display_totals(self):
        answered = self.answers.get_answered(questions=self.quiz)
        correctly_answered = self.answers.get_correctly_answered(
            questions=self.quiz)
        la = len(answered)
        lc = len(correctly_answered)
        print('answered {} of {} questions'.format(la, len(self.quiz)))
        print(('of the answered questions, {} ({:.2f}) were answered correctly'
               ).format(lc, float(lc)/la))
