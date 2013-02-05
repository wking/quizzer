class Question (object):
    def __init__(self, id=None, prompt=None, answer=None, help=None,
                 dependencies=None):
        if id is None:
            id = prompt
        self.id = id
        self.prompt = prompt
        self.answer = answer
        self.help = help
        if dependencies is None:
            dependencies = []
        self.dependencies = dependencies

    def __getstate__(self):
        return {
            'id': self.id,
            'prompt': self.prompt,
            'answer': self.answer,
            'help': self.help,
            'dependencies': self.dependencies,
            }

    def __setstate__(self, state):
        if 'id' not in state:
            state['id'] = state.get('prompt', None)
        if 'dependencies' not in state:
            state['dependencies'] = []
        self.__dict__.update(state)

    def check(self, answer):
        return answer == self.answer
