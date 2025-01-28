import re
import fasttext
import string
import numpy as np
from utils import preprocess_text
from SharedMemoryArray import SharedMemoryArray
from sklearn.metrics import f1_score, precision_score, recall_score

per_label_scale = [
    -0.5, -0.6, -0.5, -0.6, -0.6, 2.9, -0.5, -0.6, 4.0, 6.4, -0.5, -0.6, 4.0, -0.9, 4.0,
    2.3, 4.0, -0.9, -0.5, 4.0, -0.6, -0.4, 2.5, 4.0, 5.7, -0.6, 6.4, -0.6
]

def read_parquet(path):
    import pandas as pd
    return pd.read_parquet(path)

def download_dataset():
    splits = {
        'train': 'simplified/train-00000-of-00001.parquet',
        'validation': 'simplified/validation-00000-of-00001.parquet',
        'test': 'simplified/test-00000-of-00001.parquet',
        'raw': 'raw/train-00000-of-00001.parquet'
    }

    # Save each split to a local Parquet file
    for split, url in splits.items():
        df = pd.read_parquet("hf://datasets/google-research-datasets/go_emotions/" + url)

        # Save as a Parquet file
        df.to_parquet(f"datasets/go_emotions_{split}.parquet", index=False)
        print(f"Saved {split} split to go_emotions_{split}.parquet")

    splits = {'train': 'data/train-00000-of-00001.parquet', 'validation': 'data/validation-00000-of-00001.parquet', 'test': 'data/test-00000-of-00001.parquet'}
    for split, url in splits.items():
        df = pd.read_parquet("hf://datasets/Jsevisal/go_emotions_ekman/" + url)

        # Save as a Parquet file
        df.to_parquet(f"datasets/go_emotions_ekman_{split}.parquet", index=False)
        print(f"Saved {split} split to go_emotions_ekman_{split}.parquet")

# Map numeric labels to a single label (take the first label, or handle multi-labels if desired)
def preprocess_fasttext(dataframe, split):
    def format_labels(row):
        # If you want multi-label support, join all labels with spaces
        # e.g., "__label__2 __label__3 text"
        if 'preprocessed' in row:
            txt = preprocess_text(row['preprocessed'])
        else:
            txt = preprocess_text(row['text'])
        labels = " ".join([f"__label__{label}" for label in row['labels']])
        return f"{labels} {txt}"

    train_data = dataframe.apply(format_labels, axis=1)
    with open(f'{split}.txt', 'w+') as f:
        f.write("\n".join(train_data))
    return train_data

def train_model():
    df = pd.read_parquet("datasets/go_emotions_train.parquet")
    preprocess_fasttext(df, "train")
    # Train the FastText model
    model = fasttext.train_supervised(
        input="train.txt", epoch=500, lr=0.1, wordNgrams=5, verbose=2, dim=300,
        pretrained_vectors="wiki-news-300d-1M-subword.vec"
    )

    # Save the model
    model.save_model("go_emotions_model.bin")

    print("Model training complete!")


def compute_per_label_threshold():
    if True:
        #df = read_parquet("datasets/go_emotions_validation.parquet")
        #preprocessed = []
        #for idx, row in df.iterrows():
        #    preprocessed.append(preprocess_text(row['text']))
        #df['preprocessed'] = preprocessed
        #df.to_parquet(f"datasets/go_emotions_validation.preprocessed.parquet", index=False)

        df = read_parquet("datasets/go_emotions_validation.preprocessed.parquet")
        #df = read_parquet("datasets/go_emotions_train.preprocessed.parquet")
        #model = fasttext.load_model("go_emotions_model.ftz") #"go_emotions_model.bin")
        model = fasttext.load_model("go_emotions_model.bin")
        #model.quantize(input='train.txt', retrain=True)
        #model.save_model("go_emotions_model.ftz")


        label_to_idx ={
            f'__label__{i}':i
            for i in range(28)
        }
        y_pred = []
        y_true = []

        def encode_labels(p, conf=None):
            res = [0] * 28
            if conf is None:
                conf = [1] * 28
            for idx, i in enumerate(p):
                res[i] = conf[idx]
            return res

        for idx, row in df.iterrows():
            t = row['preprocessed']
            pred, conf = model.predict(t, k=-1)
            y_true.append(encode_labels(row['labels']))
            y_pred.append(encode_labels([label_to_idx[x] for x in pred], conf))
        arr1 = SharedMemoryArray('y_true', np.array(y_true))
        arr2 = SharedMemoryArray('y_pred', np.array(y_pred))
        y_true = arr1.array
        y_pred = arr2.array
    else:
        arr1 = SharedMemoryArray('y_true')
        arr2 = SharedMemoryArray('y_pred')
        y_true = arr1.array
        y_pred = arr2.array

    print(f"loaded arrays y_true {y_true.shape} y_pred {y_pred.shape}")
    if False:
        best_scales = [1] * 28
        for i in range(28):
            max_f1 = 0
            f1_val = 0
            for s in range(-60, 65, 1):
                scale = s/10.0
                yp = y_pred*1.0
                # scale the label
                yp[:, i] = y_pred[:,i] * (np.abs(scale)**(np.sign(scale)))
                k1_pred = np.zeros_like(y_pred)
                #convert to 1 hot encoding
                k1_pred[np.arange(y_pred.shape[0]),  np.argmax(yp, axis=1)] =1
                f1_val  = f1_val * 0.7 + 0.3 * f1_score(y_true, k1_pred, average="micro")
                if f1_val > max_f1:
                    max_f1 = f1_val
                    best_scales[i] =  scale
        print(best_scales)
    else:
        pl_scale = np.array(per_label_scale)
        y_pred_scaled = y_pred * (np.abs(pl_scale)**(np.sign(pl_scale)))
        k1_pred = np.zeros_like(y_pred)
        k1_pred[np.arange(y_pred.shape[0]),  np.argmax(y_pred_scaled, axis=1)] =1
        f1  = f1_score(y_true, k1_pred, average="micro")
        precision = precision_score(y_true, k1_pred, average="micro")
        recall = recall_score(y_true, k1_pred, average="micro")
        print(f"f1 is {f1} precision {precision}  recall {recall}")
    import pdb;pdb.set_trace()

#compute_per_label_threshold()



def validate_model():
    df = read_parquet("datasets/go_emotions_validation.preprocessed.parquet")
    model = fasttext.load_model("go_emotions_model.bin")
    preprocess_fasttext(df, "validation")

    result = model.test("validation.txt", k=5)
    print(result)
    print("Model validation complete!")

#download_dataset()
#train_model()
validate_model()
