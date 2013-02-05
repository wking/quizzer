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
