from .. import answerdb as _answerdb


class UserInterface (object):
    "Give a quiz over a generic user interface"
    def __init__(self, quiz=None, answers=None):
        self.quiz = quiz
        if answers is None:
            answers = _answerdb.AnswerDatabase()
        self.answers = answers

    def run(self):
        raise NotImplementedError()

    def display_results(self):
        raise NotImplementedError()

    def get_question(self):
        remaining = self.answers.get_unanswered(questions=self.quiz)
        if remaining:
            return remaining[0]

    def process_answer(self, question, answer):
        correct = question.check(answer)
        self.answers.add(question=question, answer=answer, correct=correct)
        return correct
