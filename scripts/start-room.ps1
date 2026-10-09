[CmdletBinding()]
param(
    [ValidateRange(1, 65535)]
    [int]$Port = 8765,
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $repo '.venv\Scripts\python.exe'
$url = "http://127.0.0.1:$Port"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Ambiente Python ausente. Execute 'uv sync --extra dev' na pasta do projeto primeiro."
}

$socket = [System.Net.Sockets.TcpClient]::new()
try {
    $socket.Connect('127.0.0.1', $Port)
    throw "A porta $Port já está em uso. Feche o outro servidor ou escolha outra com -Port."
} catch [System.Net.Sockets.SocketException] {
    # A porta está livre.
} finally {
    $socket.Dispose()
}

$server = Start-Process -FilePath $python -ArgumentList "-m backend.cli serve --port $Port" `
    -WorkingDirectory $repo -WindowStyle Hidden -PassThru

$ready = $false
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    if ($server.HasExited) { break }
    try {
        $response = Invoke-WebRequest -Uri "$url/api/health" -UseBasicParsing -TimeoutSec 1
        if ($response.StatusCode -eq 200) {
            $ready = $true
            break
        }
    } catch {
        Start-Sleep -Milliseconds 500
    }
}

if (-not $ready) {
    throw "O servidor não respondeu em $url. Verifique o ambiente Python e se a porta está livre."
}

if (-not $NoBrowser) {
    Start-Process -FilePath "$url/"
}

Write-Output "AI Operations Room em $url/ (PID $($server.Id))."
