$headers = @{
    'Content-Type' = 'application/json'
}
$body = '{
    "contents": [{
        "parts": [{
            "text": "What is Gemini?"
        }]
    }]
}'
$APItoken = '<api_token_from_google_AI_studio>'
$URI = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=' + $APItoken
$response = Invoke-WebRequest -Uri $URI `
    -Method 'POST' `
    -Headers $headers `
    -Body $body
$response.Content
