# Runs Selenium tests with VISIBLE Chrome and generates a dashboard report

$projectDir = "c:\Users\harit\Desktop\CSE SEM 5\Software Engineering\Jenkins\jenkins-project"
$python     = "C:\Users\harit\AppData\Local\Programs\Python\Python311\python.exe"

Set-Location $projectDir

Write-Host "`n Starting Flask app..." -ForegroundColor Cyan
$flask = Start-Process -FilePath $python -ArgumentList "app.py" `
         -PassThru -WindowStyle Minimized

Start-Sleep -Seconds 2
Write-Host " Flask running on http://localhost:5000" -ForegroundColor Green
Write-Host " Starting Selenium (browser will open)...`n" -ForegroundColor Yellow

$env:HEADLESS = "false"
$env:APP_URL  = "http://localhost:5000"

& $python -m pytest test_selenium.py -v

Write-Host "`n Generating report dashboard..." -ForegroundColor Cyan
& $python generate_report.py

Write-Host " Stopping Flask..." -ForegroundColor Yellow
Stop-Process -Id $flask.Id -Force -ErrorAction SilentlyContinue

Write-Host " Done!`n" -ForegroundColor Green
