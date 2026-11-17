$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$env:DEBUG = 'True'
& .\.venv\Scripts\python.exe manage.py process_training_jobs
exit $LASTEXITCODE
