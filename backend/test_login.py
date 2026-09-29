import httpx
api_url = "http://127.0.0.1:8000/api/v1"
res = httpx.post(f"{api_url}/auth/login", json={"email": "admin@gmail.com", "password": "Girisuri@310"})
print(res.status_code)
print(res.text)
