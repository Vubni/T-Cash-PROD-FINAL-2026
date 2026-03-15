from unittest.mock import patch
import json


async def test_register_admin_success(aiohttp_client, app):
    admin_data = {"login": "newadmin", "password": "password123"}

    with patch("functions.admin_users.create_admin") as mock_register:
        mock_register.return_value = {"admin_id": 5, "login": "newadmin", "approved": False}

        client = await aiohttp_client(app)
        resp = await client.request(
            "POST",
            "/api/v1/admin/auth/register",
            headers={"Content-Type": "application/json"},
            data=json.dumps(admin_data),
        )

        assert resp.status == 201
        data = await resp.json()
        assert data["admin_id"] == 5


async def test_login_admin_success(aiohttp_client, app):
    login_data = {"login": "admin", "password": "password123"}

    with patch("functions.admin_users.authenticate_admin") as mock_verify:
        mock_verify.return_value = {
            "admin_id": 1,
            "login": "admin",
            "approved": True,
            "main_admin": False,
        }

        client = await aiohttp_client(app)
        resp = await client.request(
            "POST",
            "/api/v1/admin/auth/login",
            headers={"Content-Type": "application/json"},
            data=json.dumps(login_data),
        )

        assert resp.status == 200
        data = await resp.json()
        assert data["admin_id"] == 1


async def test_approve_admin_success(aiohttp_client, app):
    approve_data = {"admin_id": 2}

    with patch("functions.admin_users.set_admin_approved") as mock_approve:
        mock_approve.return_value = {
            "admin_id": 2,
            "login": "admin2",
            "main_admin": False,
            "approved": True,
        }

        client = await aiohttp_client(app)
        resp = await client.request(
            "POST",
            "/api/v1/admin/auth/approve",
            headers={"Content-Type": "application/json", "Authorization": "Bearer main_token"},
            data=json.dumps(approve_data),
        )

        assert resp.status == 200
