# Ranking Algorithm base on Word Embedding

---

This algorithm ranks query's embedding vs. existing embeddings. 

required package: 

- [jiagu](https://pypi.org/project/jiagu/)
- [jieba](https://pypi.org/project/jieba/)
- [pkuseg](https://pypi.org/project/pkuseg/)
- [tencentcloud](https://cloud.tencent.com/document/sdk/Python)

required API access: 

- [Tencent NLP API](https://cloud.tencent.com/product/nlp)

---

## python_scripts/generate_embedding.py 

    generate_vector(query)
    
This function accepts an query as a input and return it's corresponding embedding. 

    First, use jieba to segment the query and generate a lit of words. 
    Second, use jieba, jiagu and pkuseg to determine that part of speech for each word 
    Only those that are noun and Chinese are kept (majority vote is utilized)
    Third, query tencentAPI for each word and calculate a mid-point of all embeddings 
    Finally, the average embedding is returned 

## python_scripts/get_closest_titles.py 

    search_title(query, return_size=20)

This function accepts query and return_size(defualt=20), and return a list of titles that are closest to the query's embedding 

    First, call generate_vector() to get the embedding of the pass-in query. 
    Then, with access to existing embedding database, it calculates the euclidean distance
    between input embedding and existing embedding 
    Finally, sort the distance and return the smallest 20(return_size) items. 