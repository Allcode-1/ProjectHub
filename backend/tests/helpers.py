DEFAULT_PASSWORD = "secret123"


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register_user(
    client,
    username: str,
    email: str | None = None,
    password: str = DEFAULT_PASSWORD,
) -> dict:
    response = client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email or f"{username}@example.com",
            "password": password,
        },
    )
    assert response.status_code == 201, response.json()
    return response.json()


def login_user(
    client,
    username: str,
    password: str = DEFAULT_PASSWORD,
) -> dict:
    response = client.post(
        "/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200, response.json()
    return response.json()


def register_and_login(
    client,
    username: str,
    email: str | None = None,
    password: str = DEFAULT_PASSWORD,
) -> tuple[dict, dict]:
    user = register_user(client, username=username, email=email, password=password)
    tokens = login_user(client, username=username, password=password)
    return user, tokens


def create_project(
    client,
    access_token: str,
    name: str = "Mobile app",
    description: str | None = "Mobile app for google",
) -> dict:
    response = client.post(
        "/api/v1/projects/",
        json={"name": name, "description": description},
        headers=auth_headers(access_token),
    )
    assert response.status_code == 201, response.json()
    return response.json()


def create_sprint(
    client,
    access_token: str,
    project_id: int,
    name: str = "Sprint 1",
    description: str | None = "First sprint",
    starts_at: str | None = None,
) -> dict:
    payload = {"name": name, "description": description}
    if starts_at is not None:
        payload["starts_at"] = starts_at

    response = client.post(
        f"/api/v1/projects/{project_id}/sprints/",
        json=payload,
        headers=auth_headers(access_token),
    )
    assert response.status_code == 201, response.json()
    return response.json()


def create_task(
    client,
    access_token: str,
    project_id: int,
    sprint_id: int,
    title: str = "Build API",
    description: str | None = "Build useful API",
    worker_id: int | None = None,
) -> dict:
    payload = {
        "title": title,
        "description": description,
        "worker_id": worker_id,
    }
    response = client.post(
        f"/api/v1/projects/{project_id}/sprints/{sprint_id}/tasks/",
        json=payload,
        headers=auth_headers(access_token),
    )
    assert response.status_code == 201, response.json()
    return response.json()


def invite_user(
    client,
    access_token: str,
    project_id: int,
    recipient_id: int,
    access_level: str = "worker",
) -> dict:
    response = client.post(
        f"/api/v1/projects/{project_id}/invites/users/{recipient_id}",
        json={"access_level": access_level},
        headers=auth_headers(access_token),
    )
    assert response.status_code == 201, response.json()
    return response.json()


def accept_invite(client, access_token: str, invite_id: int) -> dict:
    response = client.patch(
        f"/api/v1/invites/accept/{invite_id}",
        headers=auth_headers(access_token),
    )
    assert response.status_code == 200, response.json()
    return response.json()


def invite_and_accept_member(
    client,
    owner_access_token: str,
    member_access_token: str,
    project_id: int,
    member_id: int,
    access_level: str,
) -> dict:
    invite = invite_user(
        client,
        owner_access_token,
        project_id,
        member_id,
        access_level=access_level,
    )
    return accept_invite(client, member_access_token, invite["id"])
