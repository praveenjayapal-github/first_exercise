from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities_state():
    original_state = deepcopy(activities)
    yield
    activities.clear()
    activities.update(deepcopy(original_state))


def test_root_redirects_to_static_index():
    # Arrange is handled by the app state fixture
    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data():
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")
    data = response.json()

    # Assert
    assert response.status_code == 200
    assert expected_activity in data
    assert "participants" in data[expected_activity]
    assert isinstance(data[expected_activity]["participants"], list)


def test_signup_adds_new_participant():
    # Arrange
    activity_name = "Chess Club"
    new_email = "teststudent@mergington.edu"
    initial_count = len(activities[activity_name]["participants"])

    # Act
    response = client.post(
        f"/activities/{quote(activity_name)}/signup?email={quote(new_email)}"
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {new_email} for {activity_name}"
    assert len(activities[activity_name]["participants"]) == initial_count + 1
    assert new_email in activities[activity_name]["participants"]


def test_duplicate_signup_returns_bad_request():
    # Arrange
    activity_name = "Chess Club"
    existing_email = activities[activity_name]["participants"][0]
    initial_count = len(activities[activity_name]["participants"])

    # Act
    response = client.post(
        f"/activities/{quote(activity_name)}/signup?email={quote(existing_email)}"
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert len(activities[activity_name]["participants"]) == initial_count


def test_remove_participant_updates_activity():
    # Arrange
    activity_name = "Chess Club"
    participant = activities[activity_name]["participants"][0]
    initial_count = len(activities[activity_name]["participants"])

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name)}/participants/{quote(participant)}"
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {participant} from {activity_name}"
    assert len(activities[activity_name]["participants"]) == initial_count - 1
    assert participant not in activities[activity_name]["participants"]


def test_remove_missing_participant_returns_not_found():
    # Arrange
    activity_name = "Chess Club"
    missing_email = "missingstudent@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name)}/participants/{quote(missing_email)}"
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"
