import os
import sys
import signal
import threading
from .settings import app, db
from .database import Post, Label
from .post_fetcher import fetch_posts_for_label, post_fetching_worker
from flask import jsonify, request

def start_streamer():
    from server import data_stream
    from server.data_filter import operations_callback
    stream_stop_event = threading.Event()
    stream_thread = threading.Thread(
        target=data_stream.run, args=('test', operations_callback, stream_stop_event,)
    )
    stream_thread.start()


    def sigint_handler(*_):
        print('Stopping data stream...')
        #stream_stop_event.set()
        sys.exit(0)


    signal.signal(signal.SIGINT, sigint_handler)

@app.route('/api/posts/labeling', methods=['GET'])
def get_posts_with_lowest_labels():
    label_type = request.args.get('label_type', type=int)
    limit = request.args.get('limit', type=int, default=100)

    if label_type is None:
        return jsonify({"error": "label_type parameter is required."}), 400
    result = fetch_posts_for_label(label_type, limit)
    return jsonify(result), 200

@app.route('/api/labels/', methods=['POST'])
def bulk_add_labels():
    label_type = request.args.get('label_type', type=int)

    if label_type is None:
        return jsonify({"error": "label_type parameter is required."}), 400

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

        # Create the label and append to the list
        new_label = Label(
            label_type=label_type,
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
    return jsonify(result), 200


if not os.getenv("SKIP_WORKERS"):
    all_workers = [post_fetching_worker]

    for worker in all_workers:
        t = threading.Thread(target=worker)
        t.daemon=True
        t.start()
