$base = 'http://127.0.0.1:8000'
Invoke-RestMethod -Uri "$base/health" -Method Get
