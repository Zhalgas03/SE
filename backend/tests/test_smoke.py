import io
import json
import pytest
from app import create_app, db
from models.trip import Trip, VotingRule, Vote
from models import Trip as Trip_, VotingRule as VotingRule_, Vote as Vote_
from datetime import datetime, timezone

@pytest.fixture
def client():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    })
    with app.app_context():
        from models.trip import Trip, VotingRule, Vote  # Import models here
        db.create_all()
        with app.test_client() as client:
            yield client
        db.session.remove()
        db.drop_all()

def test_root(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'OK' in response.data

def make_trip(client):
    pdf_content = b"%PDF-1.4 test pdf file"
    data = {
        'title': 'Test Trip',
        'voting_rules': json.dumps({'threshold': 1, 'min_votes': 1, 'max_votes': 1}),
        'pdf': (io.BytesIO(pdf_content), 'test.pdf')
    }
    resp = client.post('/api/save_trip', data=data, content_type='multipart/form-data')
    assert resp.status_code == 201
    trip_id = resp.get_json()['trip_id']
    return trip_id

def test_save_trip(client):
    trip_id = make_trip(client)
    assert isinstance(trip_id, int)

def test_get_trip(client):
    trip_id = make_trip(client)
    resp = client.get(f'/api/get_trip/{trip_id}')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['trip_id'] == trip_id
    assert 'download_url' in data
    assert data['status'] == 'approved' or data['status'] == 'pending'

def test_vote_and_duplicate(client):
    trip_id = make_trip(client)
    vote_data = {'trip_id': trip_id, 'session_token': 'abc123', 'value': 1}
    resp = client.post('/api/vote', json=vote_data)
    assert resp.status_code == 201
    # Duplicate vote
    resp2 = client.post('/api/vote', json=vote_data)
    assert resp2.status_code == 409

def test_vote_status(client):
    trip_id = make_trip(client)
    # No votes yet
    resp = client.get(f'/api/vote_status/{trip_id}')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'pending'
    # Add a vote
    vote_data = {'trip_id': trip_id, 'session_token': 'abc123', 'value': 1}
    client.post('/api/vote', json=vote_data)
    resp2 = client.get(f'/api/vote_status/{trip_id}')
    data2 = resp2.get_json()
    assert data2['status'] == 'approved' or data2['status'] == 'pending'

    trip = db.session.get(Trip, trip_id) 