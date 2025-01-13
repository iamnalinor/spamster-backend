from io import BytesIO

from . import client, temp_task, temp_user, temp_workspace


def test_task_files():
    # Create test user, workspace and task
    with (
        temp_user() as token,
        temp_workspace(token) as workspace_id,
        temp_task(token, workspace_id) as task_id,
    ):
        headers = {"Authorization": f"Bearer {token}"}

        # Check files are empty initially
        response = client.get(f"/tasks/{task_id}/files", headers=headers)
        assert response.status_code == 200
        assert response.json() == []

        # Create test files in memory
        file1 = BytesIO(b"test content")
        file2 = BytesIO(b"test image data")

        # Upload two files
        files = [
            ("files", ("1.txt", file1, "text/plain")),
            ("files", ("42.jpg", file2, "image/jpeg")),
        ]
        response = client.patch(
            f"/tasks/{task_id}/upload-file", files=files, headers=headers
        )
        assert response.status_code == 200
        assert response.json()["count"] == 2

        # Check files list shows both files
        response = client.get(f"/tasks/{task_id}/files", headers=headers)
        assert response.status_code == 200
        files_list = response.json()
        assert len(files_list) == 2
        assert files_list[0]["name"] == "1.txt"
        assert files_list[1]["name"] == "42.jpg"

        # Download and verify each file
        for i in range(2):
            response = client.get(f"/tasks/{task_id}/files/{i}", headers=headers)
            assert response.status_code == 200
            assert "Content-Disposition" in response.headers

        # Upload third file
        file3 = BytesIO(b"third file content")
        files = [("files", ("3.doc", file3, "application/msword"))]
        response = client.patch(
            f"/tasks/{task_id}/upload-file", files=files, headers=headers
        )
        assert response.status_code == 200

        # Check files list shows all three files
        response = client.get(f"/tasks/{task_id}/files", headers=headers)
        assert response.status_code == 200
        files_list = response.json()
        assert len(files_list) == 3
        assert files_list[2]["name"] == "3.doc"

        # Delete second file (42.jpg)
        second_file_id = files_list[1]["id"]
        response = client.delete(
            f"/tasks/{task_id}/files/{second_file_id}", headers=headers
        )
        assert response.status_code == 200

        # Verify updated files list
        response = client.get(f"/tasks/{task_id}/files", headers=headers)
        assert response.status_code == 200
        files_list = response.json()
        assert len(files_list) == 2
        assert files_list[0]["name"] == "1.txt"
        assert files_list[1]["name"] == "3.doc"
