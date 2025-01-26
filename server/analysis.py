import faiss
import re
import pandas as pd
import random
from collections import defaultdict
from playhouse.shortcuts import model_to_dict
import pickle
import fasttext
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
#from sentence_transformers import SentenceTransformer
import pickle
import os
from sklearn.decomposition import PCA
from collections import defaultdict
import json
sentences = ["This is an example sentence", "Each sentence is converted"]
#sentence_transformer = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
import pdb;pdb.set_trace()


def fetch_all_posts():
    from server.database import db, Post
    posts = list(Post.select(Post.uri, Post.reply_parent, Post.reply_root, Post.text).dicts())  # Query all rows from the Post table
    df = pd.DataFrame(posts)
    # Save the DataFrame to a Parquet file
    df.to_parquet("stream_sample.parquet", engine='pyarrow', index=False)
    return df

def organize_posts(df):
    # Mappings
    post_to_replies = defaultdict(list)  # reply_parent -> [child_uris]
    root_to_posts = defaultdict(list)    # reply_root -> [descendant_uris]
    replied_posts = set()                # Set to track replied-to posts
    uri_to_text = {}

    uris = df['uri']

    # Iterate through DataFrame rows
    for _, post in df.iterrows():
        uri = post['uri']
        reply_parent = post['reply_parent']
        reply_root = post['reply_root']
        text = post['text']
        uri_to_text[uri] = text

        # Map replies to parent
        if reply_parent:
            post_to_replies[reply_parent].append(uri)
            replied_posts.add(reply_parent)

        # Map all posts to their root
        if reply_root:
            root_to_posts[reply_root].append(uri)

    # Find posts without replies (use set for faster lookup)
    posts_without_replies = uris[~uris.isin(replied_posts)].tolist()

    return post_to_replies, root_to_posts, posts_without_replies, uri_to_text

# Regular expression for non-ASCII characters
non_ascii_pattern = re.compile(r"[^\x00-\x7F]")
def preprocess(text):
    text = (re.sub(r"([.!?,'/()])", r" \1 ", text)  # Add spaces around specific punctuation characters
        .lower()  # Convert to lowercase
        .strip()  # Remove leading and trailing spaces
        .replace("  ", " ")  # Replace double spaces with a single space
        .replace("  ", " ")  # Ensure spaces are clean
    )
    text = "".join([f" {char} " if non_ascii_pattern.match(char) else char for char in text])  # Add spaces around non-ASCII characters
    text = text.replace('\n', ' ')
    return text

embedding_model = fasttext.load_model("models/cc.en.300.bin")
print("loaded embedding model")

embedding_map = {}

def get_embedding(text):
    text = preprocess(text)
    if text not in embedding_map:
        #embedding_map[text] = sentence_transformer.encode([text])[0]
        embedding_map[text] = embedding_model.get_sentence_vector(text)
    return embedding_map[text]

def train_predict_mean_reply_embedding(
    post_to_replies,
    uri_to_text,
    iterations=3,
    output_dir="models",
):
    """
    Train a supervised model to predict the mean embedding of replies from post text embeddings.

    Args:
        post_to_replies (dict): Mapping of post URIs to their reply URIs.
        uri_to_text (dict): Mapping of URIs to text.
        initial_embedding_model_path (str): Path to the pretrained FastText model for embeddings.
        iterations (int): Number of training iterations.
        output_dir (str): Directory to save trained models and metrics.

    Returns:
        str: Path to the final trained model.
    """
    os.makedirs(output_dir, exist_ok=True)
    current_embedding_model_path = ""
    use_ridge_model = False
    ridge_model = None

    for iteration in range(1, iterations + 1):
        print(f"Starting iteration {iteration}...")

        # Step 1: Load the appropriate embedding model

        # Step 2: Prepare training data
        X = []
        y = []

        for post_uri, reply_uris in post_to_replies.items():
            if not reply_uris or post_uri not in uri_to_text:
                continue

            # Get the post embedding
            post_embedding = get_embedding(uri_to_text[post_uri])
            if ridge_model:
                post_embedding = ridge_model.predict(post_embedding.reshape(1, -1))[0]

            # Compute the mean reply embedding
            reply_embeddings = []
            for reply_uri in reply_uris:
                if reply_uri in uri_to_text:
                    embedding = get_embedding(uri_to_text[reply_uri])
                    if ridge_model:
                        reply_embeddings.append(
                            ridge_model.predict(embedding.reshape(1, -1))[0]
                        )
                    else:
                        reply_embeddings.append(embedding)

            if reply_embeddings:
                mean_reply_embedding = np.mean(reply_embeddings, axis=0)
                X.append(post_embedding)
                y.append(mean_reply_embedding)

        X = np.array(X)
        y = np.array(y)

        # Step 3: Train a regression model
        print(f"Training model with {len(X)} samples...")
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
        ridge_model = Ridge(alpha=1.0)  # Ridge regression for simplicity
        ridge_model.fit(X_train, y_train)

        # Step 4: Evaluate the model
        y_pred = ridge_model.predict(X_val)
        mse = mean_squared_error(y_val, y_pred)
        print(f"Iteration {iteration}: Validation MSE = {mse}")

        # Step 5: Save the model
        current_embedding_model_path = os.path.join(output_dir, f"model_iteration_{iteration}.pkl")
        with open(current_embedding_model_path, "wb") as f:
            pickle.dump(ridge_model, f)

        print(f"Iteration {iteration}: Model saved to {current_embedding_model_path}")

    print(f"Final model saved at {current_embedding_model_path}")
    return current_embedding_model_path

def evaluate_embeddings_at_iteration(iteration, uri_to_text, model_dir="models", sample_size=100):
    """
    Evaluate a trained model at a specific iteration by generating embeddings for sample sentences.

    Args:
        iteration (int): The iteration number to evaluate.
        uri_to_text (dict): Mapping of URIs to text.
        model_dir (str): Directory where models are saved.
        sample_size (int): Number of sentences to sample for evaluation.

    Returns:
        list: A list of tuples containing text and its generated embedding.
    """
    # Load the model for the specified iteration
    if iteration>0:
        model_path = f"{model_dir}/model_iteration_{iteration}.pkl"
        try:
            with open(model_path, "rb") as f:
                model = pickle.load(f)
        except FileNotFoundError:
            raise ValueError(f"Model for iteration {iteration} not found at {model_path}.")

        print(f"Evaluating embeddings at iteration {iteration}...")

    # Sample sentences for evaluation
    sampled_uris = random.sample(list(uri_to_text.keys()), min(sample_size, len(uri_to_text)))
    embeddings = []

    average_embedding_norm = 0

    for uri in sampled_uris:
        text = uri_to_text[uri]
        embedding = get_embedding(text)
        if iteration >0:
            embedding = model.predict(embedding.reshape(1, -1))[0]
        embeddings.append((text, embedding))
        average_embedding_norm += np.linalg.norm(embedding)

    average_embedding_norm/=len(sampled_uris)

    # Optionally print the sampled texts and embeddings
    print(f"Average embedding norm: {average_embedding_norm}")

    return embeddings


def reduce_embedding_dimensions(embeddings, target_dim=6):
    """
    Reduce the dimensionality of embedding vectors using product quantization.

    Args:
        embeddings (list): A list of tuples containing text and their embedding vectors.
        target_dim (int): The target dimension for the reduced embeddings (number of centroids).

    Returns:
        list: A list of tuples with text and reduced-dimension embeddings.
    """
    # Extract embeddings from the input list
    original_vectors = np.array([embedding for _, embedding in embeddings])

    # Get the original dimension of the embeddings
    original_dim = original_vectors.shape[1]

    # Ensure the subvector dimension divides evenly
    # Initialize the FAISS Product Quantizer (PQ)
    pq = faiss.IndexPQ(original_dim, target_dim, 8)

    # Train PQ on the original vectors
    pq.train(original_vectors)

    # Quantize the original embeddings
    quantized_embeddings = pq.sa_encode(original_vectors)

    # Combine the quantized embeddings with their corresponding text
    reduced_embeddings = [
        (text, quantized_embedding) for (text, _), quantized_embedding in zip(embeddings, quantized_embeddings)
    ]

    return reduced_embeddings, pq

def save_reduced_embeddings_to_json_flat(reduced_embeddings, output_file):
    """
    Save reduced embeddings and their corresponding text into a flat JSON format.

    Args:
        reduced_embeddings (list): A list of tuples with text and reduced embeddings.
        output_file (str): Path to the output JSON file.
    """
    # Prepare data in a flat format
    data_to_save = {text: embedding.tolist() for text, embedding in reduced_embeddings}

    # Save to a JSON file
    with open(output_file, "w") as json_file:
        json.dump(data_to_save, json_file)

    print(f"Reduced embeddings saved to {output_file}")

def visualize_embeddings_with_tsne(reduced_embeddings, perplexity=30, learning_rate=200, n_iter=1000, figsize=(12, 8)):
    """
    Run t-SNE on the embeddings and visualize the text at the corresponding coordinates.

    Args:
        embeddings (list or numpy.ndarray): Array of shape (n_samples, embedding_dim).
        texts (list of str): List of text corresponding to each embedding.
        perplexity (int): Perplexity parameter for t-SNE.
        learning_rate (float): Learning rate parameter for t-SNE.
        n_iter (int): Number of iterations for optimization.
        figsize (tuple): Size of the resulting plot.
    """
    # Convert embeddings to numpy array if not already
    texts = [item[0] for item in reduced_embeddings]
    embeddings = np.array([item[1] for item in reduced_embeddings])

    # Run t-SNE
    tsne = TSNE(n_components=2, perplexity=perplexity, learning_rate=learning_rate, n_iter=n_iter, random_state=42)
    tsne_results = tsne.fit_transform(embeddings)

    # Plot t-SNE results
    plt.figure(figsize=figsize)
    for i, (x, y) in enumerate(tsne_results):
        plt.scatter(x, y, s=30, alpha=0.6)  # Add scatter point
        plt.text(x, y, texts[i], fontsize=8, alpha=0.8)  # Add text label

    plt.title("t-SNE Visualization of Embeddings")
    plt.xlabel("t-SNE Component 1")
    plt.ylabel("t-SNE Component 2")
    plt.grid(True, alpha=0.3)
    plt.show()

#fetch_all_posts()
print("reading...")
df = pd.read_parquet("stream_sample.parquet", engine='pyarrow')
print("organizing...")

post_to_replies, root_to_posts, posts_without_replies, uri_to_text= organize_posts(df)
print("training...")
#train_predict_mean_reply_embedding(post_to_replies, uri_to_text, 1)
for itr in range(0, 1):
    all_embeddings = evaluate_embeddings_at_iteration(itr, uri_to_text, sample_size = 30000)
    #reduced_embeddings, _ = reduce_embedding_dimensions(all_embeddings, 30)
    #visualize_embeddings_with_tsne(reduced_embeddings)
    output_file_path = f"reduced_embeddings_flat_{itr}.json"
    save_reduced_embeddings_to_json_flat(all_embeddings, output_file_path)

import pdb;pdb.set_trace()
