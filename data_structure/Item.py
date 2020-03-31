class Item:

    def __init__(self, frequency: int):
        self.frequency = frequency
        self.concepts_fillers_list = list()

    def increment_frequency(self):
        self.frequency += 1

    def add_to_list(self, obj: tuple):
        self.concepts_fillers_list.append(obj)

    def __lt__(self, other):
        return self.frequency < other.frequency

    def __gt__(self, other):
        return self.frequency > other.frequency

    def __repr__(self):
        return f'[{self.frequency}, {self.concepts_fillers_list}]'

    def __str__(self):
        return repr(self)
