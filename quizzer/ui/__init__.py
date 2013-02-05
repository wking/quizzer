class UserInterface (object):
    "Give a quiz over a generic user interface"
    def __init__(self, quiz=None, answers=None):
        self.quiz = quiz
        if answers is None:
            answers = {}
        self.answers = answers

    def run(self):
        raise NotImplementedError()

    def get_question(self):
        remaining = [q for q in self.quiz if q not in self.answers]
        if remaining:
            return remaining[0]

    def process_answer(self, question, answer):
        if question not in self.answers:
            self.answers[question] = []
        correct = question.check(answer)
        self.answers[question].append({
                'answer': answer,
                'correct': correct,
                })
        return correct
