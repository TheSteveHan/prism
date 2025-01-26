import re
import fasttext
import pandas as pd

def download_dataset():
    splits = {
        'train': 'simplified/train-00000-of-00001.parquet',
        'validation': 'simplified/validation-00000-of-00001.parquet',
        'test': 'simplified/test-00000-of-00001.parquet'
    }
    df = pd.read_parquet("hf://datasets/google-research-datasets/go_emotions/" + splits["train"])
    # Specify the splits you want to save (e.g., "train", "test", "validation")

    # Save each split to a local Parquet file
    for split, url in splits.items():
        df = pd.read_parquet("hf://datasets/google-research-datasets/go_emotions/" + url)

        # Save as a Parquet file
        df.to_parquet(f"datasets/go_emotions_{split}.parquet", index=False)
        print(f"Saved {split} split to go_emotions_{split}.parquet")

non_ascii_pattern = re.compile(r"[^\x00-\x7F]")
# Map numeric labels to a single label (take the first label, or handle multi-labels if desired)
def preprocess_fasttext(dataframe, split):
    def format_labels(row):
        # If you want multi-label support, join all labels with spaces
        # e.g., "__label__2 __label__3 text"
        text = (re.sub(r"([.!?,'/()])", r" \1 ", row['text'])  # Add spaces around specific punctuation characters
            .lower()  # Convert to lowercase
            .strip()  # Remove leading and trailing spaces
            .replace("  ", " ")  # Replace double spaces with a single space
            .replace("  ", " ")  # Ensure spaces are clean
        )
        text = "".join([f" {char} " if non_ascii_pattern.match(char) else char for char in text])  # Add spaces around non-ASCII characters
        text = text.replace('\n', ' ')
        labels = " ".join([f"__label__{label}" for label in row['labels']])
        return f"{labels} {row['text']}"

    train_data = dataframe.apply(format_labels, axis=1)
    with open(f'{split}.txt', 'w+') as f:
        f.write("\n".join(train_data))
    return train_data

def train_model():
    df = pd.read_parquet("datasets/go_emotions_train.parquet")
    preprocess_fasttext(df, "train")
    # Train the FastText model
    model = fasttext.train_supervised(
        input="train.txt", epoch=5000, lr=0.1, wordNgrams=2, verbose=2, dim=300,
        pretrained_vectors="wiki-news-300d-1M-subword.vec"
    )

    # Save the model
    model.save_model("go_emotions_model.bin")

    print("Model training complete!")

def validate_model():
    df = pd.read_parquet("datasets/go_emotions_validation.parquet")
    model = fasttext.load_model("go_emotions_model.bin")
    preprocess_fasttext(df, "validation")

    result = model.test("validation.txt")
    print(result)
    print("Model validation complete!")

train_model()
validate_model()
