import numpy as np
import os
import fasttext
import requests
from utils import preprocess_text
import time

go_emotions_classes = [
    "admiration",
    "amusement",
    "anger",
    "annoyance",
    "approval",
    "caring",
    "confusion",
    "curiosity",
    "desire",
    "disappointment",
    "disapproval",
    "disgust",
    "embarrassment",
    "excitement",
    "fear",
    "gratitude",
    "grief",
    "joy",
    "love",
    "nervousness",
    "optimism",
    "pride",
    "realization",
    "relief",
    "remorse",
    "sadness",
    "surprise",
    "neutral"
]

label_to_idx = {
    f'__label__{idx}': idx
    for idx, cls in enumerate(go_emotions_classes)
}

per_label_scale = np.array([
    -0.5, -0.6, -0.5, -0.6, -0.6, 2.9, -0.5, -0.6, 4.0, 6.4, -0.5, -0.6, 4.0, -0.9, 4.0,
    2.3, 4.0, -0.9, -0.5, 4.0, -0.6, -0.4, 2.5, 4.0, 5.7, -0.6, 6.4, -0.6
])
per_label_scale = np.abs(per_label_scale)**np.sign(per_label_scale)

def convert_result_to_labels(post_id, res):
    data = []
    v_label = np.zeros(28)
    # make the label vector
    for l, c in zip(*res):
        v_label[label_to_idx[l]] = c
    orig_scale = np.linalg.norm(v_label)
    if orig_scale == 0:
        return []
    v_label *= per_label_scale
    v_label = v_label / np.linalg.norm(v_label) * orig_scale

    max_label_count = 5
    # Find the largest 5 values in v_label
    labels = np.argsort(v_label)[-max_label_count:][::-1]
    confs = v_label[labels]
    total_conf = 0
    for l, c in zip(labels, confs):
        total_conf += c
        data.append({
            "confidence": c,
            "value": int(l),
            "post_id": post_id,
            "src": "FT_V0"
        })
        if total_conf > 0.5:
            break
    return data

def debug_labels(data, post):
    print(post['text'])
    msg = "\t".join([
        f'{go_emotions_classes[x["value"]]}:{x["confidence"]:0.2f}'
        for x in data
    ])
    print(msg)



SERVER_URL=os.getenv("SEVER_URL", "http://localhost:8008")
model = fasttext.load_model("/tmp/go_emotions_model.bin")
print("loaded model")
while True:
    try:
        res = requests.get(SERVER_URL+"/api/posts/labeling?label_type=1")
        posts = res.json()
        all_results = []
        for post in posts:
            res = model.predict(preprocess_text(post['text']), k=-1)
            data = convert_result_to_labels(post['post_id'], res)
            all_results += data
            debug_labels(data, post)
        print(f"generated {len(all_results)}")
        res = requests.post(SERVER_URL+"/api/labels/?label_type=1", json=all_results)
    except requests.exceptions.ConnectionError:
        time.sleep(1)
        pass
