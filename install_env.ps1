# -----------------------------------------------------------
# HaiXiaoTang Desktop Pet - Standalone Environment Config Script
# Function: Download Embedded Python, config pip, install requirements
# -----------------------------------------------------------

$ErrorActionPreference = "Stop"
$CurrentDir = Get-Location
$RuntimeDir = "$CurrentDir\runtime"
$PythonUrl = "https://www.python.org/ftp/python/3.10.11/python-3.10.11-embed-amd64.zip"
$GetPipUrl = "https://bootstrap.pypa.io/get-pip.py"

Write-Host ">>> Start building env..." -ForegroundColor Cyan

# 1. Create runtime dir
if (-not (Test-Path $RuntimeDir)) {
    New-Item -ItemType Directory -Path $RuntimeDir | Out-Null
    Write-Host "[1/5] Create runtime dir done" -ForegroundColor Green
} else {
    Write-Host "[1/5] runtime dir exists, skip" -ForegroundColor Yellow
}

# 2. Download Python
$ZipPath = "$RuntimeDir\python.zip"
if (-not (Test-Path "$RuntimeDir\python.exe")) {
    Write-Host "[2/5] Downloading Python 3.10 (approx 10MB)..."
    try {
        Invoke-WebRequest -Uri $PythonUrl -OutFile $ZipPath
        
        Write-Host "      Unzipping..."
        Expand-Archive -Path $ZipPath -DestinationPath $RuntimeDir -Force
        Remove-Item $ZipPath
        Write-Host "      Python download and unzip done" -ForegroundColor Green
    } catch {
        Write-Host "Download failed. Please check network." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[2/5] Python exists, skip download" -ForegroundColor Yellow
}

# 3. Fix python310._pth
$PthFile = "$RuntimeDir\python310._pth"
if (Test-Path $PthFile) {
    $Content = Get-Content $PthFile
    if ($Content -notcontains "import site") {
        Add-Content -Path $PthFile -Value "import site"
        Write-Host "[3/5] Fixed ._pth file config" -ForegroundColor Green
    }
}

# 4. Install pip
if (-not (Test-Path "$RuntimeDir\Scripts\pip.exe")) {
    Write-Host "[4/5] Downloading and installing pip..."
    try {
        Invoke-WebRequest -Uri $GetPipUrl -OutFile "$RuntimeDir\get-pip.py"
        Start-Process -FilePath "$RuntimeDir\python.exe" -ArgumentList "$RuntimeDir\get-pip.py" -Wait -NoNewWindow
        Remove-Item "$RuntimeDir\get-pip.py"
        Write-Host "      pip install done" -ForegroundColor Green
    } catch {
        Write-Host "pip install failed." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[4/5] pip exists, skip install" -ForegroundColor Yellow
}

# 5. Install requirements
$ReqFile = "$CurrentDir\requirements.txt"
if (Test-Path $ReqFile) {
    Write-Host "[5/5] Installing dependencies (this may take a few minutes)..." -ForegroundColor Cyan
    $PipExe = "$RuntimeDir\Scripts\pip.exe"
    try {
        # --- FIX: install build tools first because minimal python lacks them ---
        Write-Host "      Installing build tools first..." -ForegroundColor Gray
        Start-Process -FilePath $PipExe -ArgumentList "install wheel setuptools scikit-build-core cmake --no-warn-script-location" -Wait -NoNewWindow
        
        Write-Host "      Installing main requirements..." -ForegroundColor Gray
        # Using --prefer-binary to avoid compiling from source if a wheel exists
        $Proc = Start-Process -FilePath $PipExe -ArgumentList "install -r `"$ReqFile`" --no-warn-script-location --prefer-binary" -Wait -NoNewWindow -PassThru
        
        if ($Proc.ExitCode -eq 0) {
            Write-Host "      Dependencies install done" -ForegroundColor Green
        } else {
            Write-Host "      Dependencies install exited with code $($Proc.ExitCode)" -ForegroundColor Red
            Write-Host "      Common fix: Install 'Visual Studio Build Tools' if compilation is required." -ForegroundColor Yellow
            # Don't say success if it failed
            exit 1 
        }
    } catch {
        Write-Host "Dependencies install failed." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[Warning] requirements.txt not found, skip install" -ForegroundColor Red
}

Write-Host "`n>>> Build Success!" -ForegroundColor Cyan
Write-Host "You can now distribute this folder."
Write-Host "Users can run Start_Pet.bat directly." -ForegroundColor White
Write-Host "Press any key to exit..."
$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") | Out-Null
