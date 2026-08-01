from backend.tests.helpers import (
    accept_invite,
    auth_headers,
    create_project,
    create_sprint,
    invite_and_accept_member,
    invite_user,
    register_and_login,
)


def _project_ids(projects: list[dict]) -> list[int]:
    return [project["id"] for project in projects]


def _sprint_ids(sprints: list[dict]) -> list[int]:
    return [sprint["id"] for sprint in sprints]


def test_accept_invite_invalidates_recipient_project_list_cache(client):
    _, owner_tokens = register_and_login(client, username="owner")
    recipient, recipient_tokens = register_and_login(client, username="worker")
    project = create_project(client, owner_tokens["access_token"])

    cached_empty_projects = client.get(
        "/api/v1/projects/",
        headers=auth_headers(recipient_tokens["access_token"]),
    )
    invite = invite_user(
        client,
        owner_tokens["access_token"],
        project["id"],
        recipient["id"],
        access_level="worker",
    )
    accept_invite(client, recipient_tokens["access_token"], invite["id"])
    fresh_projects = client.get(
        "/api/v1/projects/",
        headers=auth_headers(recipient_tokens["access_token"]),
    )

    assert cached_empty_projects.status_code == 200
    assert cached_empty_projects.json() == []
    assert fresh_projects.status_code == 200
    assert _project_ids(fresh_projects.json()) == [project["id"]]


def test_project_update_invalidates_owner_and_member_project_list_cache(client):
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

    owner_cached_projects = client.get(
        "/api/v1/projects/",
        headers=auth_headers(owner_tokens["access_token"]),
    )
    member_cached_projects = client.get(
        "/api/v1/projects/",
        headers=auth_headers(member_tokens["access_token"]),
    )
    update_response = client.patch(
        f"/api/v1/projects/{project['id']}",
        json={"name": "Renamed project"},
        headers=auth_headers(owner_tokens["access_token"]),
    )
    owner_fresh_projects = client.get(
        "/api/v1/projects/",
        headers=auth_headers(owner_tokens["access_token"]),
    )
    member_fresh_projects = client.get(
        "/api/v1/projects/",
        headers=auth_headers(member_tokens["access_token"]),
    )

    assert owner_cached_projects.status_code == 200
    assert member_cached_projects.status_code == 200
    assert update_response.status_code == 200
    assert owner_fresh_projects.json()[0]["name"] == "Renamed project"
    assert member_fresh_projects.json()[0]["name"] == "Renamed project"


def test_project_delete_invalidates_owner_and_member_project_list_cache(client):
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

    owner_cached_projects = client.get(
        "/api/v1/projects/",
        headers=auth_headers(owner_tokens["access_token"]),
    )
    member_cached_projects = client.get(
        "/api/v1/projects/",
        headers=auth_headers(member_tokens["access_token"]),
    )
    delete_response = client.delete(
        f"/api/v1/projects/{project['id']}",
        headers=auth_headers(owner_tokens["access_token"]),
    )
    owner_fresh_projects = client.get(
        "/api/v1/projects/",
        headers=auth_headers(owner_tokens["access_token"]),
    )
    member_fresh_projects = client.get(
        "/api/v1/projects/",
        headers=auth_headers(member_tokens["access_token"]),
    )

    assert owner_cached_projects.status_code == 200
    assert member_cached_projects.status_code == 200
    assert delete_response.status_code == 204
    assert owner_fresh_projects.json() == []
    assert member_fresh_projects.json() == []


def test_sprint_actions_invalidate_project_sprint_list_cache(client):
    _, owner_tokens = register_and_login(client, username="owner")
    project = create_project(client, owner_tokens["access_token"])

    cached_empty_sprints = client.get(
        f"/api/v1/projects/{project['id']}/sprints/",
        headers=auth_headers(owner_tokens["access_token"]),
    )
    sprint = create_sprint(
        client,
        owner_tokens["access_token"],
        project["id"],
        starts_at="2035-01-01T00:00:00Z",
    )
    sprints_after_create = client.get(
        f"/api/v1/projects/{project['id']}/sprints/",
        headers=auth_headers(owner_tokens["access_token"]),
    )
    update_response = client.patch(
        f"/api/v1/projects/{project['id']}/sprints/{sprint['id']}",
        json={"name": "Renamed sprint"},
        headers=auth_headers(owner_tokens["access_token"]),
    )
    sprints_after_update = client.get(
        f"/api/v1/projects/{project['id']}/sprints/",
        headers=auth_headers(owner_tokens["access_token"]),
    )
    start_response = client.patch(
        f"/api/v1/projects/{project['id']}/sprints/{sprint['id']}/start",
        headers=auth_headers(owner_tokens["access_token"]),
    )
    sprints_after_start = client.get(
        f"/api/v1/projects/{project['id']}/sprints/",
        headers=auth_headers(owner_tokens["access_token"]),
    )
    close_response = client.patch(
        f"/api/v1/projects/{project['id']}/sprints/{sprint['id']}/close",
        headers=auth_headers(owner_tokens["access_token"]),
    )
    sprints_after_close = client.get(
        f"/api/v1/projects/{project['id']}/sprints/",
        headers=auth_headers(owner_tokens["access_token"]),
    )
    delete_response = client.delete(
        f"/api/v1/projects/{project['id']}/sprints/{sprint['id']}",
        headers=auth_headers(owner_tokens["access_token"]),
    )
    sprints_after_delete = client.get(
        f"/api/v1/projects/{project['id']}/sprints/",
        headers=auth_headers(owner_tokens["access_token"]),
    )

    assert cached_empty_sprints.status_code == 200
    assert cached_empty_sprints.json() == []
    assert _sprint_ids(sprints_after_create.json()) == [sprint["id"]]
    assert update_response.status_code == 200
    assert sprints_after_update.json()[0]["name"] == "Renamed sprint"
    assert start_response.status_code == 200
    assert sprints_after_start.json()[0]["status"] == "active"
    assert close_response.status_code == 200
    assert sprints_after_close.json()[0]["status"] == "closed"
    assert delete_response.status_code == 204
    assert sprints_after_delete.json() == []
