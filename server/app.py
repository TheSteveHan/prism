import os
from collections import defaultdict
import sys
import signal
import threading
from .settings import app, db, compress, cache
from .database import Post, Label
from .post_fetcher import fetch_posts_for_label, post_fetching_worker
from flask import jsonify, request
from .state import SERVER_STATE
from sqlalchemy.sql import func
from sqlalchemy.orm import aliased



def start_streamer():
    from server import data_stream
    from server.data_filter import operations_callback
    stream_stop_event = threading.Event()
    stream_thread = threading.Thread(
        target=data_stream.run, args=('test', operations_callback, stream_stop_event,)
    )
    stream_thread.daemon = True
    stream_thread.start()


    def sigint_handler(*_):
        print('Stopping data stream...')
        #stream_stop_event.set()
        sys.exit(0)


    signal.signal(signal.SIGINT, sigint_handler)

@app.route('/api/server-state', methods=['GET'])
def get_server_state():
    return jsonify(SERVER_STATE)

@app.route('/api/posts/labeling', methods=['GET'])
def get_posts_with_lowest_labels():
    label_type = request.args.get('label_type', type=int)
    limit = request.args.get('limit', type=int, default=100)

    if label_type is None:
        return jsonify({"error": "label_type parameter is required."}), 400
    result = fetch_posts_for_label(label_type, limit)
    return jsonify(result), 200

@app.route('/api/posts/recent', methods=['GET'])
@compress.compressed()
@cache.cached(timeout=36000)
def get_recent_posts():
    labels_subquery = db.session.query(
        Label.post_id,
        func.array_agg(Label.value).label("label_values"),
        func.array_agg(Label.confidence).label("confidences"),
        func.array_agg(Label.label_type).label("label_types"),
    ).group_by(Label.post_id).order_by(Label.post_id.desc()).limit(40000).subquery()

    # Create an alias for the subquery
    Labels = aliased(labels_subquery)

    posts_with_lables = (
        db.session.query(
                Post.id,
                Post.text,
                Labels.c.label_values,
                Labels.c.confidences,
                Labels.c.label_types,
            )
            .filter(func.length(Post.text)>35)
            .join(Labels, Labels.c.post_id == Post.id)
            .all()
    )
    results= [ ]
    for pid, txt, lv, lc, lt in posts_with_lables:
        if len(txt)<35:
            continue
        labels = defaultdict(list)
        for v, c, t in zip(lv, lc, lt):
            labels[t].append((v, c))
        results.append({
            'i': pid,
            't': txt,
            'l': labels
        })

    return jsonify(results), 200

@app.route('/api/labels/', methods=['POST'])
def bulk_add_labels():
    label_type = request.args.get('label_type', type=int)


    # Get the list of labels from the JSON body
    labels_data = request.get_json()

    if not labels_data:
        return jsonify({"error": "No label data provided."}), 400

    # List to hold the new label instances to be added
    new_labels = []

    for label_info in labels_data:
        # Ensure each label has necessary fields
        if 'confidence' not in label_info or 'value' not in label_info or 'post_id' not in label_info:
            return jsonify({"error": "Missing required fields in one of the labels."}), 400
        if label_type is None and 'label_type' not in label_info:
            return jsonify({"error": "Missing label type in one of the labels. You can specify a global label type in args"}), 400
        # Create the label and append to the list
        new_label = Label(
            label_type=label_type or label_info["label_type"],
            confidence=label_info['confidence'],
            value=label_info['value'],
            post_id=label_info['post_id'],
            src=label_info.get('src', 'default')  # Default source if not provided
        )
        new_labels.append(new_label)

    try:
        # Add all new labels to the session and commit
        db.session.add_all(new_labels)
        db.session.commit()

        return jsonify({"message": "Labels added successfully.", "count": len(new_labels)}), 201

    except Exception as e:
        print(e)
        db.session.rollback()  # In case of error, rollback transaction
        return jsonify({"error": str(e)}), 500
    return "ok", 200


if os.getenv("RUN_STREAMER"):
    start_streamer()

if not os.getenv("SKIP_WORKERS"):
    all_workers = [post_fetching_worker]

    for worker in all_workers:
        t = threading.Thread(target=worker)
        t.daemon=True
        t.start()
