import logging
from collections import defaultdict

from atproto import AtUri, CAR, firehose_models, FirehoseSubscribeReposClient, models, parse_subscribe_repos_message
from atproto.exceptions import FirehoseError

from server.database import SubscriptionState
from server.logger import logger
from server.settings import db, app

_INTERESTED_RECORDS = {
    models.AppBskyFeedLike: models.ids.AppBskyFeedLike,
    models.AppBskyFeedPost: models.ids.AppBskyFeedPost,
    models.AppBskyGraphFollow: models.ids.AppBskyGraphFollow,
}


def _get_ops_by_type(commit: models.ComAtprotoSyncSubscribeRepos.Commit) -> defaultdict:
    operation_by_type = defaultdict(lambda: {'created': [], 'deleted': []})

    car = CAR.from_bytes(commit.blocks)
    for op in commit.ops:
        if op.action == 'update':
            # we are not interested in updates
            continue

        uri = AtUri.from_str(f'at://{commit.repo}/{op.path}')

        if op.action == 'create':
            if not op.cid:
                continue

            create_info = {'uri': str(uri), 'cid': str(op.cid), 'author': commit.repo}

            record_raw_data = car.blocks.get(op.cid)
            if not record_raw_data:
                continue

            record = models.get_or_create(record_raw_data, strict=False)
            if record is None:  # unknown record (out of bsky lexicon)
                continue

            for record_type, record_nsid in _INTERESTED_RECORDS.items():
                if uri.collection == record_nsid and models.is_record_type(record, record_type):
                    operation_by_type[record_nsid]['created'].append({'record': record, **create_info})
                    break

        if op.action == 'delete':
            operation_by_type[uri.collection]['deleted'].append({'uri': str(uri)})

    return operation_by_type


def run(name, operations_callback, stream_stop_event=None):
    print("running stream")
    with app.app_context():
        while stream_stop_event is None or not stream_stop_event.is_set():
            try:
                _run(name, operations_callback, stream_stop_event)
            except FirehoseError as e:
                logger.error(f'Firehose error: {e}. Reconnecting to the firehose.')
            except Exception as e:
                logger.error(e)
                pass


def _run(name, operations_callback, stream_stop_event=None):
    state = SubscriptionState.query.filter(SubscriptionState.service == name).first()

    params = None
    if state:
        params = models.ComAtprotoSyncSubscribeRepos.Params(cursor=state.cursor)

    client = FirehoseSubscribeReposClient(params)

    if not state:
        db.session.add(SubscriptionState(service=name, cursor=0))
        db.session.commit()

    def on_message_handler(message: firehose_models.MessageFrame) -> None:
        # stop on next message if requested
        if stream_stop_event and stream_stop_event.is_set():
            client.stop()
            return

        commit = parse_subscribe_repos_message(message)
        if not isinstance(commit, models.ComAtprotoSyncSubscribeRepos.Commit):
            return


        # update stored state every ~1k events
        if commit.seq % 1000 == 0:  # lower value could lead to performance issues
            logger.debug(f'Updated cursor for {name} to {commit.seq}')
            client.update_params(models.ComAtprotoSyncSubscribeRepos.Params(cursor=commit.seq))
            SubscriptionState.query.filter_by(service=name).update({'cursor':commit.seq})
            db.session.commit()


        if not commit.blocks:
            return

        operations_callback(_get_ops_by_type(commit))

    client.start(on_message_handler)


