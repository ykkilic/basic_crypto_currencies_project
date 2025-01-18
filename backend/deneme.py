import requests

headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'tr,en-US;q=0.9,en;q=0.8',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImFkbWluQGFkbWluLmNvbSIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTczNTgxOTYwNH0.qkqrP--IoIgE7vtuH3i7bExfObi1AY4eFHrN6xwO4uA',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json',
    'Origin': 'http://46.31.77.149:3000',
    'Referer': 'http://46.31.77.149:3000/',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'X-Current-URL': 'http://46.31.77.149:3000/dashboard',
}

params = {
    'coinCurrency': 'btc',
    'timeFrame': 'one-month',
}

response = requests.get('http://46.31.77.149:8000/crypto/export-excel', params=params, headers=headers, verify=False)

print(response.content)
print(response.headers)
print(response.status_code)