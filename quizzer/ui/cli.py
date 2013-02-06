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

try:
    import readline as _readline
except ImportError as _readline_import_error:
    _readline = None

from . import UserInterface


class CommandLineInterface (UserInterface):
    def run(self):
        while True:
            question = self.get_question()
            if not question:
                break
            print(question.format_prompt())
            if question.multiline:
                answers = []
            while True:
                try:
                    answer = input('? ')
                except EOFError:
                    answer = 'quit'
                a = answer.strip().lower()
                if a in ['q', 'quit']:
                    print()
                    return
                if a in ['?', 'help']:
                    print()
                    print(question.format_prompt())
                    print(question.help)
                    continue
                if question.multiline:
                    answers.append(answer)
                    if not a:
                        break
                else:
                    break
            if question.multiline:
                answer = answers
            correct = self.process_answer(question=question, answer=answer)
            if correct:
                print('correct\n')
            else:
                print('incorrect\n')

    def display_results(self):
        print('results:')
        for question in self.quiz:
            if question.id in self.answers:
                self.display_result(question=question)
                print()
        self.display_totals()

    def display_result(self, question):
        answers = self.answers.get(question.id, [])
        print('question:')
        print('  {}'.format(question.format_prompt(newline='\n  ')))
        la = len(answers)
        lc = len([a for a in answers if a['correct']])
        print('answers: {}/{} ({:.2f})'.format(lc, la, float(lc)/la))
        for answer in answers:
            if answer['correct']:
                correct = 'correct'
            else:
                correct = 'incorrect'
            print('  you answered: {}'.format(answer['answer']))
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
