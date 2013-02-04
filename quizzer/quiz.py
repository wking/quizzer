class Quiz (list):
    def __init__(self, questions=None):
        if questions is None:
            questions = []
        super(Quiz, self).__init__(questions)

    def load(self):
        pass

    def save(self):
        pass
