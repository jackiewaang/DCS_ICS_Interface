import numpy as np
import json

data = np.load('assets/REF2014_ALL-SpaCy_NER_output_dict-en_core_web_sm.npy', allow_pickle=True).item()

with open('case_study_ner_entities.json', 'w') as f:
    json.dump(data, f)