import pandas as pd
from vlmeval.smp import *

LAST_MODIFIED = 231126000000

class TSVDataset:

    def __init__(self, dataset='MMBench', data_root=None, img_root=None):

        self.data_root = data_root if data_root is not None else LMUDataRoot()
        assert osp.exists(self.data_root)

        self.dataset = dataset
        self.dataset_URLs = {
            'MMBench': "https://opencompass.openxlab.space/utils/VLMEval/MMBench.tsv", 
            'MMBench_CN': "https://opencompass.openxlab.space/utils/VLMEval/MMBench_CN.tsv", 
            'CCBench': "https://opencompass.openxlab.space/utils/VLMEval/CCBench.tsv", 
            'MME': "https://opencompass.openxlab.space/utils/VLMEval/MME.tsv", 
            'SEEDBench_IMG': "https://opencompass.openxlab.space/utils/VLMEval/SEEDBench_IMG.tsv", 
        }
        url = self.dataset_URLs[dataset]
        file_name = url.split('/')[-1]
        data_path = osp.join(self.data_root, file_name)

        if osp.exists(data_path) and int(last_modified(data_path)) > LAST_MODIFIED:
            pass
        else:
            warnings.warn("The dataset tsv is not downloaded")
            download_file(url, data_path)

        data = load(data_path)
        image_map = {x: y for x, y in zip(data['index'], data['image'])}
        for k, v in image_map.items():
            if k >= 1000000 and self.dataset in ['MMBench', 'MMBench_CN', 'CCBench']:
                image_map[k] = image_map[k % 1000000]
            elif k % 2 == 1 and self.dataset in ['MME']:
                image_map[k] = image_map[k - 1]
        data['image'] = [image_map[k] for k in data['index']]
        self.data = data

        img_root = img_root if img_root is not None else 'images'
        img_root = osp.join(img_root, self.dataset)
        os.makedirs(img_root, exist_ok=True)
        self.img_root = img_root

    def build_prompt(self, line, dataset=None):
        if dataset is None:
            dataset = self.dataset

        if isinstance(line, int):
            line = self.data.iloc[line]

        tgt_path = osp.join(self.img_root, f"{line['index']}.jpg")
        if not osp.exists(tgt_path):
            decode_base64_to_image_file(line['image'], tgt_path)
        
        if dataset == 'MME':
            prompt = line['question']
        elif dataset in ['MMBench', 'MMBench_CN', 'CCBench', 'SEEDBench']:
            question = line['question']
            option_candidate = ['A', 'B', 'C', 'D', 'E']
            options = {
                cand: line[cand]
                for cand in option_candidate
                if cand in line and not pd.isna(line[cand])
            }
            options_prompt = 'Options:\n'
            for key, item in options.items():
                options_prompt += f'{key}. {item}\n'
            hint = line['hint'] if ('hint' in line and not pd.isna(line['hint'])) else None
            prompt = ''
            if hint is not None:
                prompt += f'Hint: {hint}\n'
            prompt += f'Question: {question}\n'
            prompt += options_prompt
            prompt += 'Please select the correct answer from the options above. \n'

        return dict(image=tgt_path, text=prompt)
    
    def display(self, line):
        if isinstance(line, int):
            line = self.data.iloc[line]
        mmqa_display(line)
    