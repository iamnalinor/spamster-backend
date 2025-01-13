from . import client, temp_task, temp_user, temp_workspace


def test_task_history_basic_flow():
    with temp_user() as user_token:
        with temp_workspace(user_token) as workspace_id:
            with temp_task(user_token, workspace_id) as task_id:
                headers = {"Authorization": f"Bearer {user_token}"}

                # Check initial history
                response = client.get(f"/tasks/{task_id}/history", headers=headers)
                assert response.status_code == 200
                history = response.json()
                assert len(history) == 1  # Initial creation event
                assert history[0]["prev"] == {
                    "name": "",
                    "description": "",
                    "subject": "",
                    "content": "",
                }

                # Make single update
                update_data = {"description": "Updated description"}
                response = client.put(
                    f"/tasks/{task_id}", json=update_data, headers=headers
                )
                assert response.status_code == 200

                # Check history after update
                response = client.get(f"/tasks/{task_id}/history", headers=headers)
                assert response.status_code == 200
                history = response.json()
                assert len(history) == 2
                assert "description" in history[1]["prev"]
                assert history[1]["data"]["description"] == "Updated description"

                # Make multiple updates
                response = client.put(
                    f"/tasks/{task_id}",
                    json={"name": "New Name", "content": "New Content"},
                    headers=headers,
                )
                assert response.status_code == 200

                response = client.put(
                    f"/tasks/{task_id}",
                    json={"subject": "New Subject"},
                    headers=headers,
                )
                assert response.status_code == 200

                # Check final history
                response = client.get(f"/tasks/{task_id}/history", headers=headers)
                assert response.status_code == 200
                history = response.json()
                assert len(history) == 4
                assert len(history[2]["prev"]) == len(history[2]["data"]) == 2
                assert len(history[3]["prev"]) == len(history[3]["data"]) == 1


def test_task_history_corner_cases():
    with temp_user() as user_token:
        with temp_workspace(user_token) as workspace_id:
            headers = {"Authorization": f"Bearer {user_token}"}

            # Test non-existent task history
            response = client.get("/tasks/99999/history", headers=headers)
            assert response.status_code == 404

            # Create minimal task
            response = client.post(
                f"/workspaces/{workspace_id}/tasks",
                json={"name": "Minimal Task", "description": ""},
                headers=headers,
            )
            assert response.status_code == 200
            task_id = response.json()["id"]

            # Test history with empty fields
            response = client.get(f"/tasks/{task_id}/history", headers=headers)
            assert response.status_code == 200
            history = response.json()
            assert len(history) == 1
            assert history[0]["prev"]["description"] == ""

            # Test update with no effective changes
            response = client.put(
                f"/tasks/{task_id}",
                json={"name": "Minimal Task"},  # Same name
                headers=headers,
            )
            assert response.status_code == 200

            response = client.get(f"/tasks/{task_id}/history", headers=headers)
            assert response.status_code == 200
            history = response.json()
            assert len(history) == 2
            assert history[1]["prev"]["name"] == "Minimal Task"
            assert history[1]["data"]["name"] == "Minimal Task"

            # Test unauthorized access
            with temp_user() as unauthorized_token:
                unauth_headers = {"Authorization": f"Bearer {unauthorized_token}"}
                response = client.get(
                    f"/tasks/{task_id}/history", headers=unauth_headers
                )
                assert response.status_code == 403
