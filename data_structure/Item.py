class Item:

    def __init__(self, frequency: int):
        self.frequency = frequency
        self.concept_bn_set = set()
        self.filler_bn_set = set()

    def increment_frequency(self):
        self.frequency += 1

    def add_to_concept_bn_set(self, obj):
        self.concept_bn_set.add(obj)

    def add_to_filler_bn_set(self, obj):
        self.filler_bn_set.add(obj)

    def __lt__(self, other):
        return self.frequency < other.counter

    def __gt__(self, other):
        return self.frequency > other.counter

    def __repr__(self):
        return f'[{self.frequency}, {self.concept_bn_set}, {self.filler_bn_set}]'

    def __str__(self):
        return repr(self)
