class Sense:

    def __init__(self, text: str, babelsynset: str):
        self.text = text
        self.babelsynset = babelsynset

    def __repr__(self):
        return f'Sense({self.text}, {self.babelsynset})'

    def __str__(self):
        return repr(self)
