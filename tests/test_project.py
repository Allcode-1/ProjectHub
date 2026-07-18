from tests.helpers import (
    auth_headers,
    create_project,
    create_sprint,
    create_task,
    invite_and_accept_member,
    register_and_login,
)


def test_create_and_list_owned_project(client):
    _, tokens = register_and_login(client, username="owner")

    project = create_project(client, tokens["access_token"])

    response = client.get(
        "/api/v1/projects/",
        headers=auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 200
    assert response.json() == [project]


def test_project_is_hidden_from_unrelated_user(client):
    _, owner_tokens = register_and_login(client, username="owner")
    _, outsider_tokens = register_and_login(client, username="outsider")
    project = create_project(client, owner_tokens["access_token"])

    response = client.get(
        f"/api/v1/projects/{project['id']}",
        headers=auth_headers(outsider_tokens["access_token"]),
    )

    assert response.status_code == 403


def test_accepted_member_can_see_project_and_member_list(client):
    _, owner_tokens = register_and_login(client, username="owner")
    member, member_tokens = register_and_login(client, username="worker")
    project = create_project(client, owner_tokens["access_token"])
    invite_and_accept_member(
        client,
        owner_tokens["access_token"],
        member_tokens["access_token"],
        project["id"],
        member["id"],
        access_level="worker",
    )

    project_response = client.get(
        f"/api/v1/projects/{project['id']}",
        headers=auth_headers(member_tokens["access_token"]),
    )
    members_response = client.get(
        f"/api/v1/projects/{project['id']}/members",
        headers=auth_headers(owner_tokens["access_token"]),
    )

    assert project_response.status_code == 200
    assert project_response.json()["id"] == project["id"]
    assert members_response.status_code == 200
    assert members_response.json()[0]["id"] == member["id"]


def test_projects_require_authentication(client):
    response = client.get("/api/v1/projects/")

    assert response.status_code == 401


def test_member_can_leave_project_and_project_cache_is_invalidated(client):
    _, owner_tokens = register_and_login(client, username="owner")
    member, member_tokens = register_and_login(client, username="worker")
    project = create_project(client, owner_tokens["access_token"])
    invite_and_accept_member(
        client,
        owner_tokens["access_token"],
        member_tokens["access_token"],
        project["id"],
        member["id"],
        access_level="worker",
    )

    cached_projects = client.get(
        "/api/v1/projects/",
        headers=auth_headers(member_tokens["access_token"]),
    )
    leave_response = client.delete(
        f"/api/v1/projects/{project['id']}/members/me",
        headers=auth_headers(member_tokens["access_token"]),
    )
    fresh_projects = client.get(
        "/api/v1/projects/",
        headers=auth_headers(member_tokens["access_token"]),
    )

    assert cached_projects.status_code == 200
    assert cached_projects.json()[0]["id"] == project["id"]
    assert leave_response.status_code == 204
    assert fresh_projects.status_code == 200
    assert fresh_projects.json() == []


def test_owner_cannot_leave_own_project(client):
    _, owner_tokens = register_and_login(client, username="owner")
    project = create_project(client, owner_tokens["access_token"])

    response = client.delete(
        f"/api/v1/projects/{project['id']}/members/me",
        headers=auth_headers(owner_tokens["access_token"]),
    )

    assert response.status_code == 409


def test_worker_cannot_leave_project_with_active_assigned_task(client):
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
    create_task(
        client,
        owner_tokens["access_token"],
        project["id"],
        sprint["id"],
        worker_id=worker["id"],
    )

    response = client.delete(
        f"/api/v1/projects/{project['id']}/members/me",
        headers=auth_headers(worker_tokens["access_token"]),
    )

    assert response.status_code == 409
