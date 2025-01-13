from . import client, temp_user


def test_workspace_crud():
    with temp_user() as token:
        headers = {"Authorization": f"Bearer {token}"}

        # Create workspace
        create_data = {"name": "Test Workspace", "myRole": "product"}
        response = client.post("/workspaces", json=create_data, headers=headers)
        assert response.status_code == 200
        workspace = response.json()
        assert workspace["name"] == "Test Workspace"
        workspace_id = workspace["id"]

        # Read workspace
        response = client.get(f"/workspaces/{workspace_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["name"] == "Test Workspace"

        # Update workspace name
        update_data = {"name": "Updated Workspace"}
        response = client.put(
            f"/workspaces/{workspace_id}", json=update_data, headers=headers
        )
        assert response.status_code == 200

        # Verify update
        response = client.get(f"/workspaces/{workspace_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Workspace"


def test_workspace_access():
    with temp_user() as owner_token, temp_user() as user_b_token:
        owner_headers = {"Authorization": f"Bearer {owner_token}"}

        response = client.get("/workspaces", headers=owner_headers)
        assert response.status_code == 200
        assert len(response.json()) == 0

        # Create workspace
        create_data = {"name": "Test Workspace", "myRole": "product"}
        response = client.post("/workspaces", json=create_data, headers=owner_headers)
        assert response.status_code == 200
        workspace = response.json()
        workspace_id = workspace["id"]

        response = client.get("/workspaces", headers=owner_headers)
        assert response.status_code == 200
        assert response.json()[0]["id"] == workspace_id

        user_b_headers = {"Authorization": f"Bearer {user_b_token}"}

        # Try to access workspace as user B (should fail)
        response = client.get(f"/workspaces/{workspace_id}", headers=user_b_headers)
        assert response.status_code == 403

        # Try to access members as user B (should fail)
        response = client.get(
            f"/workspaces/{workspace_id}/members", headers=user_b_headers
        )
        assert response.status_code == 403

        # Check that initially there's only one member (owner)
        response = client.get(
            f"/workspaces/{workspace_id}/members", headers=owner_headers
        )
        assert response.status_code == 200
        members = response.json()
        assert len(members) == 1
        assert members[0]["isOwner"]

        # Get user B's login
        response = client.get("/user/me", headers=user_b_headers)
        assert response.status_code == 200
        user_b_login = response.json()["login"]

        # Grant access to user B
        grant_data = {"login": user_b_login, "role": "editor"}
        response = client.post(
            f"/workspaces/{workspace_id}/grantAccess",
            json=grant_data,
            headers=owner_headers,
        )
        assert response.status_code == 200

        # Check that user B can now read workspace
        response = client.get(f"/workspaces/{workspace_id}", headers=user_b_headers)
        assert response.status_code == 200

        # Check that user B can now read members
        response = client.get(
            f"/workspaces/{workspace_id}/members", headers=user_b_headers
        )
        assert response.status_code == 200
        members = response.json()
        assert len(members) == 2  # owner and user B
        assert any(m["isOwner"] for m in members)  # one member is owner
        assert any(
            not m["isOwner"] and m["role"] == "editor" for m in members
        )  # user B is editor
        assert members[1]["user"]["login"] == user_b_login

        # Try to update workspace as user B (should fail)
        update_data = {"name": "B's Workspace"}
        response = client.put(
            f"/workspaces/{workspace_id}", json=update_data, headers=user_b_headers
        )
        assert response.status_code == 403

        # Revoke access from user B
        revoke_data = {"login": user_b_login}
        response = client.post(
            f"/workspaces/{workspace_id}/revokeAccess",
            json=revoke_data,
            headers=owner_headers,
        )
        assert response.status_code == 200

        # Verify user B can't access workspace anymore
        response = client.get(f"/workspaces/{workspace_id}", headers=user_b_headers)
        assert response.status_code == 403

        # Verify user B can't access members anymore
        response = client.get(
            f"/workspaces/{workspace_id}/members", headers=user_b_headers
        )
        assert response.status_code == 403
