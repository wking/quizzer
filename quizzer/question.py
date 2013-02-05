class Question (object):
    def __init__(self, prompt=None, answer=None, help=None):
        self.prompt = prompt
        self.answer = answer
        self.help = help

    def __getstate__(self):
        return {
            'prompt': self.prompt,
            'answer': self.answer,
            'help': self.help,
            }

    def __setstate__(self, state):
        self.__dict__.update(state)

    def check(self, answer):
        return answer == self.answer
