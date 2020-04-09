class Item:

    def __init__(self, frequency: int):
        self.frequency = frequency
        self.concepts_fillers_list = list()
        self.examples = list()
        self.num = 0

    def increment_frequency(self):
        self.frequency += 1

    def add_to_concepts_fillers_list(self, obj: tuple):
        self.concepts_fillers_list.append(obj)

    def add_to_examples(self, obj: tuple):
        self.examples.append(obj)

    def __lt__(self, other):
        return self.frequency < other.frequency

    def __gt__(self, other):
        return self.frequency > other.frequency

    def __repr__(self):
        return f'[{self.frequency}, {self.concepts_fillers_list}, {self.examples}]'

    def __str__(self):
        return repr(self)

    def __iter__(self):
        yield self.concepts_fillers_list
        yield self.examples
        # return zip(self.concepts_fillers_list, self.examples)
