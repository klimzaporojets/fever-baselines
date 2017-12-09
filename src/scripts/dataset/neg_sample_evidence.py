import re

from common.dataset.reader import JSONLineReader
from common.util import random
from common.util.random import SimpleRandom
from retrieval.fever_doc_db import FeverDocDB
import json
from tqdm import tqdm


def useless(title):
    return  '-LRB-disambiguation-RRB-' in title.lower() or '-LRB-disambiguation_page-RRB-' in title.lower() or re.match(r'(List_of_.+)|(Index_of_.+)|(Outline_of_.+)',  title)

jlr = JSONLineReader()

docdb = FeverDocDB("data/fever/drqa.db")

idx = docdb.get_non_empty_doc_ids()
idx = list(filter(lambda item: not useless(item),tqdm(idx)))


r = SimpleRandom.get_instance()

with open("data/fever/test.ns.rand.jsonl", "w+") as f:
    for line in jlr.read("data/fever-data/test.jsonl"):
        if line["verifiable"] == "NOT ENOUGH INFO":
            ev = []
            for e in line['evidence']:
                ev.append((e[0], idx[r.next_rand(0, len(idx))], -1))
            line['evidence'] = ev
        f.write(json.dumps(line)+"\n")

with open("data/fever/dev.ns.rand.jsonl", "w+") as f:
    for line in jlr.read("data/fever-data/dev.jsonl"):
        if line["verifiable"]=="NOT ENOUGH INFO":
            ev = []
            for e in line['evidence']:
                ev.append((e[0],idx[r.next_rand(0,len(idx))],-1))
            line['evidence'] = ev
        f.write(json.dumps(line)+"\n")




with open("data/fever/train.ns.rand.jsonl", "w+") as f:
    for line in jlr.read("data/fever-data/train.jsonl"):
        if line["verifiable"] == "NOT ENOUGH INFO":
            ev = []
            for e in line['evidence']:
                ev.append((e[0], idx[r.next_rand(0, len(idx))], -1))
            line['evidence'] = ev
        f.write(json.dumps(line)+"\n")
