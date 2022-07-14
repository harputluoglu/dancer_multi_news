from rouge_score import rouge_scorer
from tqdm import tqdm
import json

import json

def sentence_selection(read_file, write_file):
    data = []

    for line in open(read_file, 'r'):
        data.append(json.loads(line))

    def preprocess(data, chosen_metric='rougeL'):
    scorer = rouge_scorer.RougeScorer([chosen_metric])
    score_thresh = 0.05

    cur_doc = 0
    cur_docs_list = []
    cur_docs_ids = []

    for i_doc, doc in tqdm(enumerate(data)):
        if cur_doc != doc['article_number'] or i_doc == len(data) - 1:
        if i_doc == len(data) - 1:
            cur_docs_list.append(doc)
        cur_docs_sentences = []
        for i, d in enumerate(cur_docs_list):
            sen = d['article_text'].strip().split("      ")
            hyp = [e for ls in sen for e in ls if ls != sen[i]]  
            hyp = ' '.join(hyp)
            cur_sens = ""
            for s in sen:
            score = scorer.score(hyp, s)
            if score[chosen_metric][0] >= score_thresh: # 0 for precision, 1 for recall, 2 for fmeasure
                cur_sens += s + "      "
            cur_docs_sentences.append(cur_sens.strip())
        assert len(cur_docs_list) == len(cur_docs_sentences)
        for i, d in enumerate(cur_docs_list):
            d['article_idx'] = i
            d['document'] = cur_docs_sentences[i]
        
        cur_docs_list = []
        cur_doc = doc['article_number']
        cur_doc += 1
        cur_docs_list.append(doc)

    preprocess(data)

    data_str = ''
    for d in data:
        data_str += json.dumps(d) + '\n'

    with open(write_file, 'r+') as f:
        f.write(data_str)

read_file = 'data/val_format.json'
write_file = 'data/val_format_ready.json'
sentence_selection(read_file, write_file)

read_file = 'data/test_format.json'
write_file = 'data/test_format_ready.json'
sentence_selection(read_file, write_file)