from tests.helpers import (
    auth_headers,
    create_project,
    create_sprint,
    create_task,
    invite_and_accept_member,
    register_and_login,
)


def setup_project_with_worker(client):
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
    sprint = create_sprint(client, owner_tokens["access_token"], project["id"])
    return owner_tokens, worker, worker_tokens, project, sprint


def test_owner_can_create_task_assigned_to_project_worker(client):
    owner_tokens, worker, _, project, sprint = setup_project_with_worker(client)

    task = create_task(
        client,
        owner_tokens["access_token"],
        project["id"],
        sprint["id"],
        worker_id=worker["id"],
    )

    assert task["worker_id"] == worker["id"]
    assert task["status"] == "todo"


def test_owner_cannot_assign_task_to_user_outside_project(client):
    _, owner_tokens = register_and_login(client, username="owner")
    outsider, _ = register_and_login(client, username="outsider")
    project = create_project(client, owner_tokens["access_token"])
    sprint = create_sprint(client, owner_tokens["access_token"], project["id"])

    response = client.post(
        f"/api/v1/projects/{project['id']}/sprints/{sprint['id']}/tasks/",
        json={
            "title": "Build API",
            "description": "Build useful API",
            "worker_id": outsider["id"],
        },
        headers=auth_headers(owner_tokens["access_token"]),
    )

    assert response.status_code == 404


def test_worker_can_take_task_send_to_review_and_owner_can_accept(client):
    owner_tokens, worker, worker_tokens, project, sprint = setup_project_with_worker(
        client
    )
    task = create_task(
        client,
        owner_tokens["access_token"],
        project["id"],
        sprint["id"],
    )

    take_response = client.patch(
        f"/api/v1/projects/{project['id']}/sprints/{sprint['id']}/tasks/"
        f"{task['id']}/take_task",
        headers=auth_headers(worker_tokens["access_token"]),
    )
    review_response = client.patch(
        f"/api/v1/projects/{project['id']}/sprints/{sprint['id']}/tasks/"
        f"{task['id']}/to_review",
        headers=auth_headers(worker_tokens["access_token"]),
    )
    accept_response = client.patch(
        f"/api/v1/projects/{project['id']}/sprints/{sprint['id']}/tasks/"
        f"{task['id']}/accept",
        headers=auth_headers(owner_tokens["access_token"]),
    )

    assert take_response.status_code == 200
    assert take_response.json()["worker_id"] == worker["id"]
    assert take_response.json()["status"] == "in_progress"
    assert review_response.status_code == 200
    assert review_response.json()["status"] == "review"
    assert accept_response.status_code == 200
    assert accept_response.json()["status"] == "done"


def test_viewer_cannot_take_task(client):
    _, owner_tokens = register_and_login(client, username="owner")
    viewer, viewer_tokens = register_and_login(client, username="viewer")
    project = create_project(client, owner_tokens["access_token"])
    invite_and_accept_member(
        client,
        owner_tokens["access_token"],
        viewer_tokens["access_token"],
        project["id"],
        viewer["id"],
        access_level="viewer",
    )
    sprint = create_sprint(client, owner_tokens["access_token"], project["id"])
    task = create_task(client, owner_tokens["access_token"], project["id"], sprint["id"])

    response = client.patch(
        f"/api/v1/projects/{project['id']}/sprints/{sprint['id']}/tasks/"
        f"{task['id']}/take_task",
        headers=auth_headers(viewer_tokens["access_token"]),
    )

    assert response.status_code == 403
