import threading
import datetime
import time
import queue
from .database import LabelType, Label, Post
from collections import deque
from .settings import db, app
class DoubleBuffer:
    def __init__(self):
        self.current_buffer = None
        self.next_buffer = None
        self.current_buffer_idx = 0
        self.lock = threading.Lock()  # Lock for thread-safe operations
        self.buffer_not_empty = threading.Condition(self.lock)  # Condition variable for non-empty buffer
        self.buffer_not_full = threading.Condition(self.lock)  # Condition variable for non-full buffer


    def get(self, batch_size):
        while self.current_buffer is None:
            with self.buffer_not_empty:
                # Wait if the buffer is empty
                self.buffer_not_empty.wait()

        items = []
        switched_buffer = False
        with self.lock:
            items += self.current_buffer[self.current_buffer_idx: self.current_buffer_idx + batch_size]
            if len(items) < batch_size:
                switched_buffer = True
                self.current_buffer = self.next_buffer
                self.next_buffer = None
                self.current_buffer_idx = 0
                try:
                    self.buffer_not_full.notify_all()
                except Exception:
                    pass
                if self.current_buffer:
                    self.current_buffer_idx = batch_size - len(items)
                    items += self.current_buffer[:self.current_buffer_idx]
            else:
                self.current_buffer_idx += batch_size

        if switched_buffer:
            try:
                self.buffer_not_full.notify_all()
            except Exception:
                pass

        return items



    def put(self, items):
        with self.lock:
            if self.current_buffer is None:
                self.current_buffer = items
            else:
                self.next_buffer = items

        # Notify consumers that the buffer is no longer empty
        try:
            self.buffer_not_empty.notify_all()
        except Exception:
            pass


posts_to_label = {}
results_ready = {}

for i in LabelType:
    posts_to_label[i] = DoubleBuffer()
    results_ready[i] = queue.Queue()

# Task queue holds (label_type, limit) pairs that tell the fetching worker what to do
task_queue = queue.Queue()

def query_for_low_conf_posts(label_type, limit):
    # Query to fetch posts with the lowest weighted label count, considering confidence and value
    with app.app_context():
        subquery = db.session.query(
            Label.post_id,
            db.func.avg(Label.confidence).label('avg_confidence')
        ).filter_by(label_type=label_type).group_by(Label.post_id).subquery()
        posts = db.session.query(Post, subquery.c.avg_confidence).outerjoin(
            subquery, Post.id == subquery.c.post_id,
        ).order_by(subquery.c.avg_confidence.asc().nullsfirst()).limit(1000).all()

    return [
        {
            "post_id": post.id,
            "text": post.text,
            "avg_confidence": avg_confidence if avg_confidence else 0
        }
        for post, avg_confidence in posts
    ]

def post_fetching_worker(max_itr =-1):
    itr = 0
    last_fetch = datetime.datetime.now()
    fetched_samples = 0
    print(f"post fetching worker started with max_itr {max_itr}")
    while True:
        try:
            label_type, limit = task_queue.get(timeout=1)  # Wait for a task if the queue is empty
            print(f"{label_type} {limit}")
            now = datetime.datetime.utcnow()
            notified = False
            if fetched_samples > limit:
                notified = True
                results_ready[label_type].put(True)
                print("notified result ready")
            # limit max fetch frequency
            if ((now - last_fetch).total_seconds() > 2 and fetched_samples < 500) or (fetched_samples<200):
                print('fetching new samples')
                results = query_for_low_conf_posts(label_type, limit)
                fetched_samples += len(results)
                print(f'fetched {len(results)} new samples, total sampples left {fetched_samples}')
                posts_to_label[label_type].put(results)
                itr += 1
            fetched_samples -= limit
            print("marrking task done")
            task_queue.task_done()  # Indicate that the task has been processed
            print("notifying result ready")
            if notified==False:
                results_ready[label_type].put(True)
                print("notified result ready")
        except queue.Empty:
            continue
        except Exception as e:
            print(e)

        if max_itr > 0 and itr > max_itr:
            break
        time.sleep(1)

    print(f"post fetching worker exited after {itr} iters")


def fetch_posts_for_label(label_type, limit):
    task = (label_type, limit)
    print("putting task")
    task_queue.put(task)
    print("pwaiting for result")
    results_ready[label_type].get()
    results_ready[label_type].task_done()
    return posts_to_label[label_type].get(limit)

