import urllib.request

try:
    with urllib.request.urlopen("http://localhost:8000/reset-stream", data=b"") as response:
        print(response.read().decode())
except Exception as e:
    print(f"Error: {e}")
