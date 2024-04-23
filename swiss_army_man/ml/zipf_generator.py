import numpy as np
from scipy.stats import zipf

# For any given dataset, for some god forsaken reason, the 2nd most popular product will be 1/2 as
# popular as the most popular product. The 3rd most popular will be 1/3 as popular as the first, and so on.
# 
# The Zipf generator takes a list and allows you to sample from it following the zipf distribution, returning
# a random choice based on this law.
class ZipfGenerator():
    def __init__(self, items, s=1.5):
        self.items = items
        self.popularity_ranks = zipf.rvs(s, size=len(items))

    def random(self):
        return np.random.choice(self.items, p=self.popularity_ranks/self.popularity_ranks.sum())