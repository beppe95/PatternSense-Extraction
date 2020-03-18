from data_structure.Sense import Sense


class SemagramAnnotation:

    def __init__(self, sense1: Sense, sense2: Sense, slot: str):
        self.sense1 = sense1
        self.sense2 = sense2
        self.slot = slot

    def __repr__(self):
        return f'SemagramAnnotation({self.sense1}, {self.sense2}, {self.slot})'

    def __str__(self):
        return repr(self)
