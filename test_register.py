import requests
import json

url = "http://127.0.0.1:8001/api/register"
data = {"username": "testuser3", "password": "testpassword3"}
headers = {"Content-Type": "application/json"}

try:
    response = requests.post(url, data=json.dumps(data), headers=headers)
    print(f"Status Code: {response.status_code}")
    print("Response JSON:")
    print(response.json())
except requests.exceptions.JSONDecodeError:
    print("Failed to decode JSON from response. Response text:")
    print(response.text)
except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
    if e.response:
        print(f"Response content: {e.response.text}")
