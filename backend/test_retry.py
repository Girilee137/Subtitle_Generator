import httpx
api_url = "http://127.0.0.1:8000/api/v1"
# 1. Login
response = httpx.post(f"{api_url}/auth/login", json={"email": "admin@gmail.com", "password": "Girisuri@310"})
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
# 2. Hit retry on the project
project_id = "adc3adf8-7dfb-413a-8e0d-d6ed0bb5435f"
res = httpx.post(f"{api_url}/projects/{project_id}/retry", headers=headers)
print(res.status_code)
print(res.text)
