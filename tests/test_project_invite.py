from tests.helpers import (
    auth_headers,
    create_project,
    invite_user,
    register_and_login,
)


def test_invite_recipient_can_read_and_accept_invite(client):
    _, owner_tokens = register_and_login(client, username="owner")
    recipient, recipient_tokens = register_and_login(client, username="worker")
    outsider, outsider_tokens = register_and_login(client, username="outsider")
    project = create_project(client, owner_tokens["access_token"])
    invite = invite_user(
        client,
        owner_tokens["access_token"],
        project["id"],
        recipient["id"],
        access_level="worker",
    )

    my_invites_response = client.get(
        "/api/v1/invites",
        headers=auth_headers(recipient_tokens["access_token"]),
    )
    read_invite_response = client.get(
        f"/api/v1/invites/{invite['id']}",
        headers=auth_headers(recipient_tokens["access_token"]),
    )
    outsider_read_response = client.get(
        f"/api/v1/invites/{invite['id']}",
        headers=auth_headers(outsider_tokens["access_token"]),
    )
    accept_response = client.patch(
        f"/api/v1/invites/accept/{invite['id']}",
        headers=auth_headers(recipient_tokens["access_token"]),
    )
    projects_response = client.get(
        "/api/v1/projects/",
        headers=auth_headers(recipient_tokens["access_token"]),
    )

    assert outsider["id"] != recipient["id"]
    assert my_invites_response.status_code == 200
    assert my_invites_response.json()[0]["id"] == invite["id"]
    assert read_invite_response.status_code == 200
    assert read_invite_response.json()["send_to"] == recipient["id"]
    assert outsider_read_response.status_code == 404
    assert accept_response.status_code == 200
    assert accept_response.json()["status"] == "accepted"
    assert projects_response.status_code == 200
    assert projects_response.json()[0]["id"] == project["id"]


def test_declined_invite_cannot_be_accepted(client):
    _, owner_tokens = register_and_login(client, username="owner")
    recipient, recipient_tokens = register_and_login(client, username="viewer")
    project = create_project(client, owner_tokens["access_token"])
    invite = invite_user(
        client,
        owner_tokens["access_token"],
        project["id"],
        recipient["id"],
        access_level="viewer",
    )

    decline_response = client.patch(
        f"/api/v1/invites/decline/{invite['id']}",
        headers=auth_headers(recipient_tokens["access_token"]),
    )
    accept_response = client.patch(
        f"/api/v1/invites/accept/{invite['id']}",
        headers=auth_headers(recipient_tokens["access_token"]),
    )

    assert decline_response.status_code == 200
    assert decline_response.json()["status"] == "declined"
    assert accept_response.status_code == 409


def test_owner_can_update_and_delete_pending_invite(client):
    _, owner_tokens = register_and_login(client, username="owner")
    recipient, _ = register_and_login(client, username="worker")
    project = create_project(client, owner_tokens["access_token"])
    invite = invite_user(
        client,
        owner_tokens["access_token"],
        project["id"],
        recipient["id"],
        access_level="viewer",
    )

    update_response = client.patch(
        f"/api/v1/projects/{project['id']}/invites/users/{recipient['id']}",
        json={"access_level": "worker"},
        headers=auth_headers(owner_tokens["access_token"]),
    )
    delete_response = client.delete(
        f"/api/v1/projects/{project['id']}/invites/users/{recipient['id']}",
        headers=auth_headers(owner_tokens["access_token"]),
    )
    read_response = client.get(
        f"/api/v1/invites/{invite['id']}",
        headers=auth_headers(owner_tokens["access_token"]),
    )

    assert update_response.status_code == 200
    assert update_response.json()["access_level"] == "worker"
    assert delete_response.status_code == 204
    assert read_response.status_code == 404
