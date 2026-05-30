"""Тесты для библиотеки."""

import datetime
from starlette.testclient import TestClient

class TestLibraryBooks:
    def test_create_and_delete_book(self, auth_client: TestClient):
        resp = auth_client.post(
            "/api/v1/books/",
            json={
                "title": "Test Book",
                "author": "Test Author",
                "isbn": "1234567890",
                "quantity_total": 10,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Test Book"
        assert data["author"] == "Test Author"
        assert data["isbn"] == "1234567890"
        assert data["quantity_total"] == 10
        book_id = data["id"]

        resp = auth_client.delete(f"/api/v1/books/{book_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("ok") is True
    
    def test_get_books(self, auth_client: TestClient):
        resp = auth_client.get("/api/v1/books/")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_get_book_by_id(self, auth_client: TestClient):
        resp = auth_client.post(
            "/api/v1/books/",
            json={
                "title": "Test Book 2",
                "author": "Test Author 2",
                "isbn": "0987654321",
                "quantity_total": 5,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        book_id = data["id"]

        resp = auth_client.get(f"/api/v1/books/{book_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == book_id
        assert data["title"] == "Test Book 2"
        assert data["author"] == "Test Author 2"
        assert data["isbn"] == "0987654321"
        assert data["quantity_total"] == 5

        resp = auth_client.delete(f"/api/v1/books/{book_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("ok") is True
    
    def test_update_book(self, auth_client: TestClient):
        resp = auth_client.post(
            "/api/v1/books/",
            json={
                "title": "Test Book 3",
                "author": "Test Author 3",
                "isbn": "1111111111",
                "quantity_total": 3,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        book_id = data["id"]

        resp = auth_client.put(
            f"/api/v1/books/{book_id}",
            json={
                "title": "Updated Test Book 3",
                "author": "Updated Test Author 3",
                "isbn": "2222222222",
                "quantity_total": 4,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == book_id
        assert data["title"] == "Updated Test Book 3"
        assert data["author"] == "Updated Test Author 3"
        assert data["isbn"] == "2222222222"
        assert data["quantity_total"] == 4

        resp = auth_client.get(f"/api/v1/books/{book_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Updated Test Book 3"
        assert data["author"] == "Updated Test Author 3"
        assert data["isbn"] == "2222222222"
        assert data["quantity_total"] == 4

        resp = auth_client.delete(f"/api/v1/books/{book_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("ok") is True

class TestLibraryLoans:
    @staticmethod
    def parse_iso_z(s: str) -> datetime.datetime:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt

    def test_issue_and_return_book(self, auth_client: TestClient):
        resp = auth_client.post(
            "/api/v1/books/",
            json={
                "title": "Loan Test Book",
                "author": "Loan Test Author",
                "isbn": "3333333333",
                "quantity_total": 2,
            })
        
        assert resp.status_code == 200
        data = resp.json()
        book_id = data["id"]

        resp = auth_client.post(
            "/api/v1/loans/",
            json={
                "book_id": book_id,
                "user_id": 1,
                "deadline": "2026-12-31T23:59:59Z",
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["book_id"] == book_id
        assert data["user_id"] == 1
        assert data["deadline"] == "2026-12-31T23:59:59"

        resp = auth_client.post(f"/api/v1/loans/return", 
                                json={
                                    "book_id": book_id, 
                                    "user_id": 1
                                })
        assert resp.status_code == 200
        data = resp.json()
        assert data["book_id"] == book_id
        assert data["user_id"] == 1
        assert data["deadline"] == "2026-12-31T23:59:59"
        
        resp = auth_client.delete(f"/api/v1/books/{book_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("ok") is True

    def test_get_user_loans(self, auth_client: TestClient):
        resp = auth_client.post(
            "/api/v1/books/",
            json={
                "title": "User Loans Test Book",
                "author": "User Loans Test Author",
                "isbn": "4444444444",
                "quantity_total": 1,
            })
        assert resp.status_code == 200
        data = resp.json()
        book_id = data["id"]

        resp = auth_client.post(
            "/api/v1/loans/",
            json={
                "book_id": book_id,
                "user_id": 1,
                "deadline": "2026-12-31T23:59:59Z",
            })
        assert resp.status_code == 200
        data = resp.json()

        resp = auth_client.get("/api/v1/loans/user/1")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[-1]["book_id"] == book_id
        assert data[-1]["user_id"] == 1
        assert data[-1]["deadline"] == "2026-12-31T23:59:59"

        resp = auth_client.post(f"/api/v1/loans/return", 
                                json={
                                    "book_id": book_id, 
                                    "user_id": 1
                                })
        assert resp.status_code == 200
        
        resp = auth_client.delete(f"/api/v1/books/{book_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("ok") is True

    def test_get_active_loans(self, auth_client: TestClient):
        resp = auth_client.post(
            "/api/v1/books/",
            json={
                "title": "Active Loans Test Book",
                "author": "Active Loans Test Author",
                "isbn": "5555555555",
                "quantity_total": 1,
            })
        assert resp.status_code == 200
        data = resp.json()
        book_id = data["id"]

        resp = auth_client.post(
            "/api/v1/loans/",
            json={
                "book_id": book_id,
                "user_id": 1,
                "deadline": "2026-12-31T23:59:59Z",
            })
        assert resp.status_code == 200
        data = resp.json()

        resp = auth_client.get("/api/v1/loans/active")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[-1]["book_id"] == book_id
        assert data[-1]["user_id"] == 1
        assert data[-1]["deadline"] == "2026-12-31T23:59:59"

        resp = auth_client.post(f"/api/v1/loans/return", 
                                json={
                                    "book_id": book_id, 
                                    "user_id": 1
                                })
        assert resp.status_code == 200
        
        resp = auth_client.delete(f"/api/v1/books/{book_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("ok") is True

    def test_overdue_loans(self, auth_client: TestClient):
        resp = auth_client.post(
            "/api/v1/books/",
            json={
                "title": "Overdue Loans Test Book",
                "author": "Overdue Loans Test Author",
                "isbn": "6666666666",
                "quantity_total": 1,
            })
        assert resp.status_code == 200
        data = resp.json()
        book_id = data["id"]

        resp = auth_client.post(
            "/api/v1/loans/",
            json={
                "book_id": book_id,
                "user_id": 1,
                "deadline": "2020-01-01T00:00:00Z",
            })
        assert resp.status_code == 200
        data = resp.json()

        resp = auth_client.get("/api/v1/loans/overdue")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[-1]["book_id"] == book_id
        assert data[-1]["user_id"] == 1
        assert data[-1]["deadline"] == "2020-01-01T00:00:00"

        resp = auth_client.post(f"/api/v1/loans/return", 
                                json={
                                    "book_id": book_id, 
                                    "user_id": 1
                                })
        assert resp.status_code == 200
        data = resp.json()
        assert data["book_id"] == book_id
        assert data["user_id"] == 1
        assert data["deadline"] == "2020-01-01T00:00:00"
        assert self.parse_iso_z(data["deadline"]) <= self.parse_iso_z("2020-01-01T00:00:00")
        assert len(data) > 0
        
        resp = auth_client.delete(f"/api/v1/books/{book_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("ok") is True