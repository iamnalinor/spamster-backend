from . import client, temp_task, temp_user, temp_workspace


def test_task_comments():
    with temp_user() as user1_token, temp_user() as user2_token:
        with temp_workspace(user1_token) as workspace_id:
            with temp_task(user1_token, workspace_id) as task_id:
                user1_headers = {"Authorization": f"Bearer {user1_token}"}
                user2_headers = {"Authorization": f"Bearer {user2_token}"}

                # Check initial comments (should be empty)
                response = client.get(
                    f"/tasks/{task_id}/comments", headers=user1_headers
                )
                assert response.status_code == 200
                comments = response.json()
                assert len(comments) == 0

                # Add comment from first user
                comment1_text = "Comment from user 1"
                response = client.post(
                    f"/tasks/{task_id}/comments",
                    json={"text": comment1_text},
                    headers=user1_headers,
                )
                assert response.status_code == 200
                comment1 = response.json()
                assert comment1["text"] == comment1_text
                assert comment1["taskId"] == task_id
                user1_id = comment1["userId"]

                # Check comments after first comment
                response = client.get(
                    f"/tasks/{task_id}/comments", headers=user1_headers
                )
                assert response.status_code == 200
                comments = response.json()
                assert len(comments) == 1
                assert comments[0]["text"] == comment1_text
                assert comments[0]["taskId"] == task_id
                assert comments[0]["userId"] == user1_id

                # Try to add comment from second user without access
                comment2_text = "Comment from user 2"
                response = client.post(
                    f"/tasks/{task_id}/comments",
                    json={"text": comment2_text},
                    headers=user2_headers,
                )
                assert response.status_code == 403

                # Get user 2's login
                response = client.get("/user/me", headers=user2_headers)
                assert response.status_code == 200
                user2_login = response.json()["login"]

                # Grant access to user 2
                grant_data = {"login": user2_login, "role": "editor"}
                response = client.post(
                    f"/workspaces/{workspace_id}/grantAccess",
                    json=grant_data,
                    headers=user1_headers,
                )
                assert response.status_code == 200

                # Now add comment from second user
                response = client.post(
                    f"/tasks/{task_id}/comments",
                    json={"text": comment2_text},
                    headers=user2_headers,
                )
                assert response.status_code == 200
                comment2 = response.json()
                assert comment2["text"] == comment2_text
                assert comment2["taskId"] == task_id
                user2_id = comment2["userId"]
                assert user2_id != user1_id

                # Check comments after second comment
                response = client.get(
                    f"/tasks/{task_id}/comments", headers=user1_headers
                )
                assert response.status_code == 200
                comments = response.json()
                assert len(comments) == 2

                # Verify both comments exist with correct data
                comments_by_user = {c["userId"]: c for c in comments}
                assert comments_by_user[user1_id]["text"] == comment1_text
                assert comments_by_user[user1_id]["taskId"] == task_id
                assert comments_by_user[user2_id]["text"] == comment2_text
                assert comments_by_user[user2_id]["taskId"] == task_id
