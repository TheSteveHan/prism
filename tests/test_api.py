import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from server.app import app, db
from server.database import Post, Label
from server.post_fetcher import post_fetching_worker
import threading

def create_test_data():
    post1 = Post(uri='post1', cid='cid1', text='Test post 1')
    post2 = Post(uri='post2', cid='cid2', text='Test post 2')

    label1 = Label(id=0, label_type=1, confidence=0.9, value=1, post=post1, src="steve")
    label2 = Label(id=1, label_type=1, confidence=0.5, value=1, post=post1, src="steve")
    label3 = Label(id=2, label_type=1, confidence=0.8, value=1, post=post2, src="ft_v0")
    label4 = Label(id=3, label_type=2, confidence=0.6, value=1, post=post2, src="ft_v0")

    db.session.add_all([post1, post2, label1, label2, label3, label4])
    db.session.commit()
    fetcher_thread = threading.Thread(target=post_fetching_worker, args=(1,))
    fetcher_thread.daemon = True
    fetcher_thread.start()


def test_labeling_endpoint(test_client):
    create_test_data()

    response = test_client.get('/api/posts/labeling?label_type=1&limit=2')
    assert response.status_code == 200

    data = response.get_json()
    assert len(data) == 2

    assert data[0]['post_id'] == 1  # Post with the lowest average confidence for type 1
    assert data[1]['post_id'] == 2

def test_invalid_label_type(test_client):
    create_test_data()
    response = test_client.get('/api/posts/labeling?limit=2')
    assert response.status_code == 400

    data = response.get_json()
    assert "error" in data
    assert data["error"] == "label_type parameter is required."

def test_no_data_for_label_type(test_client):
    create_test_data()

    response = test_client.get('/api/posts/labeling?label_type=3&limit=2')
    assert response.status_code == 200

    data = response.get_json()
    assert len(data) == 2 # all posts need to be labeled in this case


def test_bulk_add_labels(test_client):
    sample_post = Post(id=2)
    # Create mock data for labels
    labels_data = [
        {"confidence": 0.9, "value": 1, "post_id": sample_post.id, "src": "user1"},
        {"confidence": 0.8, "value": 0, "post_id": sample_post.id, "src": "user2"},
    ]

    # Send POST request to bulk add labels
    response = test_client.post('/api/labels/?label_type=1', json=labels_data)

    # Assert the response is successful
    assert response.status_code == 201
    response_data = response.get_json()
    assert response_data['message'] == "Labels added successfully."
    assert response_data['count'] == 2

    # Verify that labels were added to the database
    labels = Label.query.all()
    assert len(labels) == 2
    assert labels[0].confidence == 0.9
    assert labels[1].confidence == 0.8

def test_generate_user_submit_post(test_client):
    response = test_client.post('/api/auth/stateless-user')
    token = response.get_json()['token']
    headers = {'Authorization': f"JWT {token}"}
    response = test_client.post('/api/posts/submit', json=[{
        "uri": "https://www.youtube.com/watch?v=36L9cYkHyZM",
        "text": "some description"
    }], headers= headers)
    assert response.status_code == 201
    response = test_client.get('/api/posts/submissions', headers= headers)
    data = response.json
    assert len(data) == 1
    sid = data[0]['id']
    response = test_client.post(f'/api/posts/submissions/review/{sid}', headers=headers, json=[
        {
            'value': 1,
            'label_type': 1,
        },
        {
            'value': 0.3,
            'label_type': 2,
        },
        {
            'value': 0.2,
            'label_type': 3,
        },
        {
            'value': 1,
            'label_type': 4,
            'comment': "this is terrible"
        },
    ])
    assert response.status_code == 201
    response = test_client.get('/api/posts/recent-videos', headers= headers)
    data = response.json
    print(data)
    assert len(data) == 1

