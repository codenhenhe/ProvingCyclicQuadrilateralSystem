import os, requests

API_KEY = os.getenv("GOOGLE_API_KEY")
url = f"https://generativelanguage.googleapis.com/v1/models?key={API_KEY}"
print(requests.get(url).json())
