from . import UserInterface


class CommandLineInterface (UserInterface):
    def run(self):
        while True:
            question = self.get_question()
            if not question:
                break
            print(question.prompt)
            while True:
                answer = input('? ')
                a = answer.strip().lower()
                if a in ['q', 'quit']:
                    print()
                    return
                if a in ['?', 'help']:
                    print()
                    print(question.prompt)
                    print(question.hint)
                    continue
                break
            correct = self.process_answer(question=question, answer=answer)
            if correct:
                print('correct\n')
            else:
                print('incorrect\n')

    def display_results(self):
        print('results:')
        for question in self.quiz:
            if question in self.answers:
                for answer in self.answers[question]:
                    self.display_result(question=question, answer=answer)
        self.display_totals()

    def display_result(self, question, answer):
        if answer['correct']:
            correct = 'correct'
        else:
            correct = 'incorrect'
        print('question:     {}'.format(question.prompt))
        print('you answered: {}'.format(answer['answer']))
        print('which was:    {}'.format(correct))
        print()

    def display_totals(self):
        answered = self.get_answered()
        correctly_answered = self.get_correctly_answered()
        la = len(answered)
        lc = len(correctly_answered)
        print('answered {} of {} questions'.format(la, len(self.quiz)))
        print(('of the answered questions, {} ({:.2f}) were answered correctly'
               ).format(lc, float(lc)/la))
