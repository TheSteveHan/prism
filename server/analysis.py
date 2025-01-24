import pandas as pd
from collections import defaultdict
from server.database import db, Post
from playhouse.shortcuts import model_to_dict
import pickle

from collections import defaultdict

def fetch_all_posts():
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
    uri_to_post = {}

    # Vectorized operations for reply_parent and reply_root
    reply_parents = df['reply_parent']
    reply_roots = df['reply_root']
    uris = df['uri']

    # Map replies to parent
    for reply_parent, uri in zip(reply_parents, uris):
        if reply_parent:
            post_to_replies[reply_parent].append(uri)
            replied_posts.add(reply_parent)

    # Map all posts to their root
    for reply_root, uri in zip(reply_roots, uris):
        if reply_root:
            root_to_posts[reply_root].append(uri)

    # Find posts without replies (use set for faster lookup)
    posts_without_replies = uris[~uris.isin(replied_posts)].tolist()

    return post_to_replies, root_to_posts, posts_without_replies



fetch_all_posts()
print("reading...")
df = pd.read_parquet("stream_sample.parquet", engine='pyarrow')
print("organizing...")

post_to_replies, root_to_posts, posts_without_replies = organize_posts(df)
import pdb;pdb.set_trace()
# Print results
print("Post to Replies Mapping:")
for parent, children in post_to_replies.items():
    print(f"{parent}: {children}")

print("\nRoot to Posts Mapping:")
for root, descendants in root_to_posts.items():
    print(f"{root}: {descendants}")

print("\nPosts Without Replies:")
print(posts_without_replies)
