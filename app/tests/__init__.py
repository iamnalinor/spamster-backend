import contextlib
import secrets
from collections.abc import Iterator

from starlette.testclient import TestClient

from app.misc import app

client = TestClient(app, base_url="http://testserver/api")


@contextlib.contextmanager
def temp_user() -> Iterator[int]:
    # Generate random credentials
    username = f"test_user_{secrets.token_hex(6)}"
    password = secrets.token_urlsafe(6)
    name = f"Test User {secrets.token_hex(2)}"
    # Create user
    user_data = {"login": username, "password": password, "name": name}
    response = client.post("/user/register", json=user_data)
    assert response.status_code == 200

    token = response.json()["accessToken"]
    yield token


@contextlib.contextmanager
def temp_workspace(access_token: str, my_role: str = "product") -> Iterator[int]:
    # Create workspace with random name
    workspace_name = f"Test Workspace {secrets.token_hex(2)}"
    create_data = {"name": workspace_name, "myRole": my_role}
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.post("/workspaces", json=create_data, headers=headers)
    assert response.status_code == 200
    workspace_id = response.json()["id"]

    yield workspace_id


@contextlib.contextmanager
def temp_task(access_token: str, workspace_id: int) -> Iterator[int]:
    task_name = f"Test Task {secrets.token_hex(2)}"
    create_data = {"name": task_name, "description": "average human task description"}
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.post(
        f"/workspaces/{workspace_id}/tasks", json=create_data, headers=headers
    )
    assert response.status_code == 200
    task_id = response.json()["id"]

    yield task_id
