from . import client, temp_user, temp_workspace


def test_task_crud():
    with (
        temp_user() as owner_token,
        temp_workspace(owner_token) as workspace_id,
        temp_user() as other_token,
    ):
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # Try to get tasks as non-member (should fail)
        response = client.get(
            f"/workspaces/{workspace_id}/tasks", headers=other_headers
        )
        assert response.status_code == 403

        # Create task
        task_data = {"name": "Test Task", "description": "Test Description"}
        response = client.post(
            f"/workspaces/{workspace_id}/tasks",
            json=task_data,
            headers=owner_headers,
        )
        assert response.status_code == 200
        task = response.json()
        assert task["name"] == "Test Task"
        assert task["description"] == "Test Description"
        assert task["subject"] == ""
        assert task["content"] == ""
        task_id = task["id"]

        # Get task
        response = client.get(f"/tasks/{task_id}", headers=owner_headers)
        assert response.status_code == 200
        task = response.json()
        assert task["id"] == task_id
        assert task["name"] == "Test Task"
        assert task["description"] == "Test Description"
        assert task["subject"] == ""
        assert task["content"] == ""

        # Get tasks
        response = client.get(
            f"/workspaces/{workspace_id}/tasks", headers=owner_headers
        )
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 1
        assert tasks[0]["id"] == task_id
        assert len(tasks[0]["checks"]) == 6

        # Update task
        update_data = {
            "name": "Updated Task",
            "description": "Updated Description",
            "subject": "Test Subject",
            "content": "Test Content",
        }
        response = client.put(
            f"/tasks/{task_id}",
            json=update_data,
            headers=owner_headers,
        )
        assert response.status_code == 200
        updated_task = response.json()
        assert updated_task["name"] == "Updated Task"
        assert updated_task["description"] == "Updated Description"
        assert updated_task["subject"] == "Test Subject"
        assert updated_task["content"] == "Test Content"

        # Partial update
        partial_update = {
            "name": "Partially Updated Task",
            "subject": None,
        }
        response = client.put(
            f"/tasks/{task_id}",
            json=partial_update,
            headers=owner_headers,
        )
        assert response.status_code == 200
        partially_updated_task = response.json()
        assert partially_updated_task["name"] == "Partially Updated Task"
        assert (
            partially_updated_task["description"] == "Updated Description"
        )  # unchanged

        # Delete task
        response = client.delete(f"/tasks/{task_id}", headers=owner_headers)
        assert response.status_code == 200
        assert response.json() is True

        # Verify task is deleted
        response = client.get(
            f"/workspaces/{workspace_id}/tasks", headers=owner_headers
        )
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 0

        response = client.get(f"/tasks/{task_id}", headers=owner_headers)
        assert response.status_code == 404
