from .. import answerdb as _answerdb


class UserInterface (object):
    "Give a quiz over a generic user interface"
    def __init__(self, quiz=None, answers=None, stack=None):
        self.quiz = quiz
        if answers is None:
            answers = _answerdb.AnswerDatabase()
        self.answers = answers
        if stack is None:
            stack = quiz.leaf_questions()
        self.stack = stack

    def run(self):
        raise NotImplementedError()

    def display_results(self):
        raise NotImplementedError()

    def get_question(self):
        if self.stack:
            print(self.stack)
            return self.stack.pop(0)

    def process_answer(self, question, answer):
        correct = question.check(answer)
        self.answers.add(question=question, answer=answer, correct=correct)
        if not correct:
            self.stack.insert(0, question)
            for qid in reversed(question.dependencies):
                self.stack.insert(0, self.quiz.get(id=qid))
        return correct
