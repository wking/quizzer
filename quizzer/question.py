QUESTION_CLASS = {}


def register_question(question_class):
    QUESTION_CLASS[question_class.__name__] = question_class


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

    def __str__(self):
        return '<{} id:{!r}>'.format(type(self).__name__, self.id)

    def __repr__(self):
        return '<{} id:{!r} at {:#x}>'.format(
            type(self).__name__, self.id, id(self))

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


class NormalizedStringQuestion (Question):
    def normalize(self, string):
        return string.strip().lower()

    def check(self, answer):
        return self.normalize(answer) == self.normalize(self.answer)


for name,obj in list(locals().items()):
    if name.startswith('_'):
        continue
    try:
        subclass = issubclass(obj, Question)
    except TypeError:  # obj is not a class
        continue
    if subclass:
        register_question(obj)
del name, obj
