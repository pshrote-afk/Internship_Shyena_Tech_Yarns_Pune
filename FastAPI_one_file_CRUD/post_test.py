import requests

url = "http://127.0.0.1:8000"

data = {
"key":"Book B",
"value":"Author B"
}

response = requests.post(url,json=data)
print(response.json())