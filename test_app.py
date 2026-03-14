import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

# ── Fixtures ──────────────────────────────────────────────────────────────────

MOCK_GISTS = [
    {
        "id": "abc123",
        "description": "Hello World",
        "html_url": "https://gist.github.com/octocat/abc123",
        "files": {"hello_world.rb": {}},
        "created_at": "2010-04-14T02:15:15Z",
        "updated_at": "2011-06-20T11:34:15Z",
        "public": True,
    },
    {
        "id": "def456",
        "description": "Another gist",
        "html_url": "https://gist.github.com/octocat/def456",
        "files": {"script.py": {}, "readme.md": {}},
        "created_at": "2021-01-01T00:00:00Z",
        "updated_at": "2021-06-01T00:00:00Z",
        "public": True,
    },
]


def make_mock_response(status_code, json_data):
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    return mock


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestRootEndpoint:
    def test_root_returns_200(self):
        response = client.get("/")
        assert response.status_code == 200

    def test_root_returns_usage_message(self):
        response = client.get("/")
        assert "message" in response.json()


class TestGetUserGists:
    @patch("app.httpx.AsyncClient")
    def test_returns_gists_for_valid_user(self, mock_client_cls):
        mock_client_cls.return_value.__aenter__.return_value.get.return_value = (
            make_mock_response(200, MOCK_GISTS)
        )

        response = client.get("/octocat")

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "octocat"
        assert data["count"] == 2
        assert len(data["gists"]) == 2

    @patch("app.httpx.AsyncClient")
    def test_gist_fields_are_correct(self, mock_client_cls):
        mock_client_cls.return_value.__aenter__.return_value.get.return_value = (
            make_mock_response(200, MOCK_GISTS)
        )

        response = client.get("/octocat")
        gist = response.json()["gists"][0]

        assert gist["id"] == "abc123"
        assert gist["description"] == "Hello World"
        assert gist["url"] == "https://gist.github.com/octocat/abc123"
        assert gist["files"] == ["hello_world.rb"]
        assert gist["public"] is True

    @patch("app.httpx.AsyncClient")
    def test_gist_with_multiple_files(self, mock_client_cls):
        mock_client_cls.return_value.__aenter__.return_value.get.return_value = (
            make_mock_response(200, MOCK_GISTS)
        )

        response = client.get("/octocat")
        gist = response.json()["gists"][1]

        assert len(gist["files"]) == 2
        assert "script.py" in gist["files"]
        assert "readme.md" in gist["files"]

    @patch("app.httpx.AsyncClient")
    def test_returns_empty_list_for_user_with_no_gists(self, mock_client_cls):
        mock_client_cls.return_value.__aenter__.return_value.get.return_value = (
            make_mock_response(200, [])
        )

        response = client.get("/emptyuser")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["gists"] == []

    @patch("app.httpx.AsyncClient")
    def test_returns_404_for_unknown_user(self, mock_client_cls):
        mock_client_cls.return_value.__aenter__.return_value.get.return_value = (
            make_mock_response(404, {"message": "Not Found"})
        )

        response = client.get("/this-user-does-not-exist-xyz987")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch("app.httpx.AsyncClient")
    def test_handles_github_api_error(self, mock_client_cls):
        mock_client_cls.return_value.__aenter__.return_value.get.return_value = (
            make_mock_response(503, {})
        )

        response = client.get("/someuser")

        assert response.status_code == 503
