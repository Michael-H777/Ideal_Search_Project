# word processing 
import jiagu 
import jieba 
import pkuseg 
import jieba.posseg as jieba_seg

# tencent API 
import json
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.nlp.v20190408 import nlp_client, models

# redis API 
import redis 

# multithreading 
from concurrent.futures import ThreadPoolExecutor 

# argparse 
import argparse 

parser = argparse.ArgumentParser(description='python script that takes input from Redis, process and push result back to Redis')
parser.add_argument('-host', default='localhost', type=str, help='Redis host address')
parser.add_argument('-port', default=6379 ,type=int, help='Redis port')
parser.add_argument('-input_queue', default='task:prodcons:input_queue', type=str, help='Redis input queue name')
parser.add_argument('-output_queue', default='task:prodcons:output_queue', type=str, help='Redis output queue name')
parser.add_argument('-pool', default=4, type=int, help='Thread pool size')

args = parser.parse_args()


pku_seg = pkuseg.pkuseg(postag=True)

redis_api = redis.StrictRedis(host=args.host, port=args.port, db=0, decode_responses=True)

class word_obj:
    
    def __init__(self, word, *seg_results):
        self.word = word 
        self.is_n = sum([item == 'n' for item in seg_results]) >= 2 
        self.is_cn = all(item != 'eng' for item in seg_results) and all(not char.isdigit() for char in word)
        
    def __repr__(self):
        return self.word 
    
    __str__ = __repr__ 


def get_tencent_client():
    with open('../api_keys.txt', 'r') as filein: 
        api_id = filein.readline().partition(':')[-1].strip()
        api_secret = filein.readline().partition(':')[-1].strip()
    cred = credential.Credential(api_id, api_secret) 
    httpProfile = HttpProfile()
    httpProfile.endpoint = "nlp.tencentcloudapi.com"

    clientProfile = ClientProfile()
    clientProfile.httpProfile = httpProfile
    client = nlp_client.NlpClient(cred, "ap-guangzhou", clientProfile) 
    return client 


def generate_vector(query):
    global pku_seg, redis_api, args
    client = get_tencent_client()
    word_request = models.WordEmbeddingRequest()
    '''
    The main purpose of this function is to accept an query, segment it into nouns, 
    gather embedding of these nouns and take the average. 
    calling jieba_seg, pku_seg all have some overhead where they need to build a dictionary 
    It's be best to keep this alive, and call as a function somehow
    '''
    time_stamp, _, query = query.partition('_')
    identifier, _, query = query.partition('_')
    
    temp_result = []
    # some words cannot get segmented, need more time to investigate specific cases 
    try:
        segment_list = list(filter(lambda item: item != ' ', jieba.lcut_for_search(query)))
    except: 
        return '-1'

    # get part of speech, vote for is_noun and is_chinese
    for word in segment_list:
        jieba_pos = jieba_seg.lcut(word)
        jiagu_pos = jiagu.pos([word])
        pku_pos = pku_seg.cut(word)
        try:
            temp_result.append(word_obj(word, jieba_pos[0].flag, jiagu_pos[0], pku_pos[0][1]))
        except:
            continue
    result_cleaned = list(filter(lambda item: item.is_n and item.is_cn, temp_result))
    
    # fetch vector for each word
    vector_list = []
    for word_ins in result_cleaned: 
        current_word = word_ins.word
        try:
            params = {'Text': current_word}
            word_request.from_json_string(json.dumps(params))
            current_response = client.WordEmbedding(word_request)
            word_vector = json.loads(current_response.to_json_string())['Vector']
        except TencentCloudSDKException as error:
            print(f'\rreached exception with inner {error}')
            continue
        except: 
            client = get_tencent_client()
        vector_list.append(word_vector)
    
    query_vector = list(map(lambda item: round( sum(item)/len(item) , 5), zip(*vector_list)))
    
    redis_api.rpush(args.output_queue, f'{time_stamp}_{identifier}_{query_vector}')
    print(f'processed {time_stamp}_{identifier}_{query}, result pushed to redis')
    return None 


def main():
    global redis_api, args
    
    with ThreadPoolExecutor(max_workers=args.pool) as pool: 
        print('thread pool initialized, waiting for input')
        while True:
            query = redis_api.blpop(args.input_queue, 0)[1]
            pool.submit(generate_vector, query)
        

if __name__ == '__main__':
    main() 
