import numpy as np
from swiss_army_man.ml import normalize

class GaussianGenerator():
    def __init__(self, items):
        self.items = items
        self.distribution = normalize(np.random.normal(loc=1, scale=1, size=len(items)))
        self.probabilities = self.distribution / self.distribution.sum()

    def random(self, len=1):
        if len == 1:
            return self.one_random()
        else:
            return [self.one_random() for _ in range(len)]

    def one_random(self):
        return np.random.choice(self.items, p=self.probabilities)