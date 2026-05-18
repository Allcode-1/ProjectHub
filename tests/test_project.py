from tests.helpers import auth_headers, create_schedule, register_and_login


def test_add_project(client):
    _, tokens = register_and_login(client, username="sam")

    response = client.post(
        "/api/v1/projects/",
        json={"name": "Mobile app", "description": "Mobile app for google"},
        headers=auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "Mobile app"
    assert data["description"] == "Mobile app for google"


def test_read_own_projects(client):
    _, tokens = register_and_login(client, username="sam")
    create_schedule(client, tokens["access_token"])

    response = client.get(
        "/api/v1/projects/",
        headers=auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 200

    data = response.json()
    assert data[0]["name"] == "Mobile app"
    assert data[0]["description"] == "Mobile app for google"


def test_read_schedules_without_token(client):
    response = client.get("/api/v1/projects/")

    assert response.status_code == 401
