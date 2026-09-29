import httpx
import time

api_url = "http://127.0.0.1:8000/api/v1"

# 1. Login
response = httpx.post(f"{api_url}/auth/login", json={"email": "admin@gmail.com", "password": "Girisuri@310"})
response.raise_for_status()
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Create project
response = httpx.post(f"{api_url}/projects", json={"title": "Test GPU Transcription"}, headers=headers)
response.raise_for_status()
project_id = response.json()["project_id"]

# 3. Upload file
with open("sample_speech.wav", "rb") as f:
    files = {"file": ("sample_speech.wav", f, "audio/wav")}
    response = httpx.post(f"{api_url}/projects/{project_id}/files", headers=headers, files=files, data={"is_stored": "true"})
    response.raise_for_status()
    file_id = response.json()["file_id"]

# 4. Start processing
response = httpx.post(f"{api_url}/files/{file_id}/process", headers=headers, json={"language": "auto"})
response.raise_for_status()
job_id = response.json()["job_id"]

# 5. Poll for completion
print(f"Job {job_id} started, polling...")
while True:
    res = httpx.get(f"{api_url}/jobs/{job_id}", headers=headers)
    res.raise_for_status()
    job = res.json()
    print(f"Status: {job['status']} - {job['stage']} ({job['progress']}%)")
    if job['status'] in ['COMPLETED', 'FAILED']:
        break
    time.sleep(1)

# 6. Fetch tracks
if job['status'] == 'COMPLETED':
    res = httpx.get(f"{api_url}/files/{file_id}/tracks", headers=headers)
    res.raise_for_status()
    tracks = res.json()
    if tracks:
        track_id = tracks[0]['track_id']
        res = httpx.get(f"{api_url}/tracks/{track_id}", headers=headers)
        track = res.json()
        print("\nTranscription Result:")
        for seg in track.get("segments", []):
            print(f"[{seg['start_time']} - {seg['end_time']}] {seg['text']}")
