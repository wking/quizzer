class Question (object):
    def __init__(self, prompt=None, answer=None, help=None):
        self.prompt = prompt
        self.answer = answer
        self.help = help

    def check(self, answer):
        return answer == self.answer

