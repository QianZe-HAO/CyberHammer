# using v2rayn
$env:HTTP_PROXY = "http://127.0.0.1:10809"
$env:HTTP_PROXYS = "http://127.0.0.1:10809"
conda activate agentflow
Start-Process "http://127.0.0.1:7860/"
langflow run
