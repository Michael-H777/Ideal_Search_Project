import pickle 
from sklearn.metrics.pairwise import euclidean_distances as distance

from generate_embedding import generate_vector

    
class vector_obj:
    
    def __init__(self, id_, title, vector):
        self.id = id_ 
        self.title = title 
        self.vector = vector 
        
    def __repr__(self):
        return f'{self.id} {self.title}'
    
    __str__ = __repr__ 


def search_title(query, return_size=20):
    
    # we need to tap into existing database that contains embedding for all titles 
    # right now we can use ../title_vectors

    with open('title_vectors', 'rb') as filein: 
        title_vectors = pickle.load(filein)
    
    title_distance = []
    vector = generate_vector(query)
    for vector_ins in title_vectors: 
        # some titles does not have a valid embedding, being English etc. 
        if vector_ins.vector:
            euclidean = distance([vector, vector_ins.vector])[0].sum() 
            title_distance.append((vector_ins.title, euclidean))
    title_distance.sort(key=lambda item: item[-1])

    return title_distance[:return_size]
