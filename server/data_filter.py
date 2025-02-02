from collections import defaultdict

from atproto import models

from server.logger import logger
from server.database import db, Post
from server.state import SERVER_STATE

def operations_callback(ops: defaultdict) -> None:
    # Here we can filter, process, run ML classification, etc.
    # After our feed alg we can save posts into our DB
    # Also, we should process deleted posts to remove them from our DB and keep it in sync

    # for example, let's create our custom feed that will contain all posts that contains alf related text

    posts_to_create = []
    for created_post in ops[models.ids.AppBskyFeedPost]['created']:
        author = created_post['author']
        record = created_post['record']
        if not record.langs or len(record.langs)!=1 or ('en' not in record.langs):
            continue
        # print all texts just as demo that data stream works
        post_with_images = isinstance(record.embed, models.AppBskyEmbedImages.Main)
        inlined_text = record.text.replace('\n', ' ').replace("\0", "")
        '''
        print(
            f'NEW POST '
            f'[CREATED_AT={record.created_at}]'
            f'[AUTHOR={author}]'
            f'[WITH_IMAGE={post_with_images}]'
            f': {inlined_text}'
            ,end="\r"
        )
        '''
        # only python-related posts
        reply_root = reply_parent = None
        if record.reply:
            reply_root = record.reply.root.uri
            reply_parent = record.reply.parent.uri

        post_dict = {
            'uri': created_post['uri'],
            'cid': created_post['cid'],
            'reply_parent': reply_parent,
            'reply_root': reply_root,
            'text': record.text,
        }
        posts_to_create.append(post_dict)

    if posts_to_create:
        try:
            db.session.bulk_insert_mappings(Post, posts_to_create)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
        SERVER_STATE['TOTAL_ENTRIES'] += len(posts_to_create)
        #logger.debug(f'Added to feed: {len(posts_to_create)}')
