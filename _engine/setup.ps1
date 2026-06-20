# Setup OCR_Sistema per Windows (PowerShell).
# Uso: click destro su questo file -> "Esegui con PowerShell", oppure:
#   powershell -ExecutionPolicy Bypass -File _engine\setup.ps1
$ErrorActionPreference = "Stop"
$Engine = Split-Path -Parent $MyInvocation.MyCommand.Path
$Base   = Split-Path -Parent $Engine
Write-Host "==> OCR_Sistema in: $Base"

# --- 1. Dipendenze di sistema (una volta) ---
Write-Host "==> Verifica tesseract / ocrmypdf / ollama nel PATH..."
foreach ($t in @("tesseract","ocrmypdf","ollama")) {
  if (-not (Get-Command $t -ErrorAction SilentlyContinue)) {
    Write-Warning "Manca '$t'. Installalo prima di continuare:"
    Write-Host "   Tesseract: https://github.com/UB-Mannheim/tesseract/wiki (aggiungi la lingua 'ita')"
    Write-Host "   OCRmyPDF:  pip install ocrmypdf  (richiede Ghostscript)"
    Write-Host "   Ollama:    https://ollama.com/download/windows"
  }
}

# --- 2. Virtualenv Python + dipendenze ---
Write-Host "==> Creo virtualenv e installo dipendenze Python..."
python -m venv "$Engine\.venv"
& "$Engine\.venv\Scripts\pip.exe" install --upgrade pip
& "$Engine\.venv\Scripts\pip.exe" install -r "$Engine\requirements.txt"

# --- 3. Controllo hardware + dipendenze ---
Write-Host "==> Controllo hardware e componenti..."
& "$Engine\.venv\Scripts\python.exe" "$Engine\check.py"
$risp = Read-Host "Procedo con il download del modello LLM (~5GB)? [s/N]"
if ($risp -notin @("s","S","y","Y")) {
  Write-Host "Interrotto. Rilancia quando vuoi questo setup."
  exit 0
}

# --- 4. Modello LLM ---
Write-Host "==> Scarico il modello qwen2.5:7b (~5GB) se manca..."
try { ollama pull qwen2.5:7b } catch { Write-Warning "Esegui poi: ollama pull qwen2.5:7b" }

# --- 4. Avvio automatico al login (Task Scheduler) ---
$Pyw = "$Engine\.venv\Scripts\pythonw.exe"
$Watch = "$Engine\watch.py"
Write-Host "==> Registro l'avvio automatico al login (Task Scheduler)..."
$action  = New-ScheduledTaskAction -Execute $Pyw -Argument "`"$Watch`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
try {
  Register-ScheduledTask -TaskName "OCR_Sistema" -Action $action -Trigger $trigger -Force | Out-Null
  Start-ScheduledTask -TaskName "OCR_Sistema"
  Write-Host "==> Avvio automatico installato."
} catch {
  Write-Warning "Non sono riuscito a registrare il task. Avvio manuale: $Pyw $Watch"
}

Write-Host ""
Write-Host "==> FATTO. Metti i documenti in: $Base\inbox"
Write-Host "    Vengono processati da soli e ordinati in: $Base\archivio"
