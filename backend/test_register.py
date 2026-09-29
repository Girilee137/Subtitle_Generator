import httpx
api_url = "http://127.0.0.1:8000/api/v1"
res = httpx.post(f"{api_url}/auth/register", json={"name": "Test User", "email": "testregister@gmail.com", "password": "Password@123"})
print(res.status_code)
print(res.text)
