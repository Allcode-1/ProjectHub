from tests.helpers import (
    auth_headers,
    create_project,
    create_sprint,
    invite_and_accept_member,
    register_and_login,
)


def test_owner_can_create_list_start_close_and_delete_sprint(client):
    _, owner_tokens = register_and_login(client, username="owner")
    project = create_project(client, owner_tokens["access_token"])
    sprint = create_sprint(
        client,
        owner_tokens["access_token"],
        project["id"],
        starts_at="2035-01-01T00:00:00Z",
    )

    list_response = client.get(
        f"/api/v1/projects/{project['id']}/sprints/",
        headers=auth_headers(owner_tokens["access_token"]),
    )
    start_response = client.patch(
        f"/api/v1/projects/{project['id']}/sprints/{sprint['id']}/start",
        headers=auth_headers(owner_tokens["access_token"]),
    )
    close_response = client.patch(
        f"/api/v1/projects/{project['id']}/sprints/{sprint['id']}/close",
        headers=auth_headers(owner_tokens["access_token"]),
    )
    delete_response = client.delete(
        f"/api/v1/projects/{project['id']}/sprints/{sprint['id']}",
        headers=auth_headers(owner_tokens["access_token"]),
    )
    get_deleted_response = client.get(
        f"/api/v1/projects/{project['id']}/sprints/{sprint['id']}",
        headers=auth_headers(owner_tokens["access_token"]),
    )

    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == sprint["id"]
    assert start_response.status_code == 200
    assert start_response.json()["status"] == "active"
    assert close_response.status_code == 200
    assert close_response.json()["status"] == "closed"
    assert delete_response.status_code == 204
    assert get_deleted_response.status_code == 404


def test_worker_cannot_create_sprint(client):
    _, owner_tokens = register_and_login(client, username="owner")
    worker, worker_tokens = register_and_login(client, username="worker")
    project = create_project(client, owner_tokens["access_token"])
    invite_and_accept_member(
        client,
        owner_tokens["access_token"],
        worker_tokens["access_token"],
        project["id"],
        worker["id"],
        access_level="worker",
    )

    response = client.post(
        f"/api/v1/projects/{project['id']}/sprints/",
        json={"name": "Sprint 1", "description": "First sprint"},
        headers=auth_headers(worker_tokens["access_token"]),
    )

    assert response.status_code == 403


def test_sprint_state_machine_rejects_invalid_transitions(client):
    _, owner_tokens = register_and_login(client, username="owner")
    project = create_project(client, owner_tokens["access_token"])
    sprint = create_sprint(
        client,
        owner_tokens["access_token"],
        project["id"],
        starts_at="2035-01-01T00:00:00Z",
    )

    close_planned_response = client.patch(
        f"/api/v1/projects/{project['id']}/sprints/{sprint['id']}/close",
        headers=auth_headers(owner_tokens["access_token"]),
    )
    start_response = client.patch(
        f"/api/v1/projects/{project['id']}/sprints/{sprint['id']}/start",
        headers=auth_headers(owner_tokens["access_token"]),
    )
    start_again_response = client.patch(
        f"/api/v1/projects/{project['id']}/sprints/{sprint['id']}/start",
        headers=auth_headers(owner_tokens["access_token"]),
    )
    close_response = client.patch(
        f"/api/v1/projects/{project['id']}/sprints/{sprint['id']}/close",
        headers=auth_headers(owner_tokens["access_token"]),
    )
    update_closed_response = client.patch(
        f"/api/v1/projects/{project['id']}/sprints/{sprint['id']}",
        json={"name": "Should not update"},
        headers=auth_headers(owner_tokens["access_token"]),
    )

    assert close_planned_response.status_code == 409
    assert start_response.status_code == 200
    assert start_again_response.status_code == 409
    assert close_response.status_code == 200
    assert update_closed_response.status_code == 409


def test_sprint_update_rejects_invalid_date_range(client):
    _, owner_tokens = register_and_login(client, username="owner")
    project = create_project(client, owner_tokens["access_token"])
    sprint = create_sprint(
        client,
        owner_tokens["access_token"],
        project["id"],
        starts_at="2035-01-01T00:00:00Z",
    )

    response = client.patch(
        f"/api/v1/projects/{project['id']}/sprints/{sprint['id']}",
        json={
            "starts_at": "2035-01-10T00:00:00Z",
            "ends_at": "2035-01-09T00:00:00Z",
        },
        headers=auth_headers(owner_tokens["access_token"]),
    )

    assert response.status_code == 422
