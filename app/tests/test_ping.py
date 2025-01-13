from . import client


def test_ping_route():
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() is True
