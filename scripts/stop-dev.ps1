# Stop backend (8000) and frontend (5173) by listening port.
$ports = @(8000, 5173)
$stopped = @()

foreach ($port in $ports) {
    $pids = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($procId in $pids) {
        if ($procId -and $stopped -notcontains $procId) {
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
            $stopped += $procId
            Write-Host "  Stopped process on port ${port} (PID $procId)"
        }
    }
}

if ($stopped.Count -eq 0) {
    Write-Host "  No servers listening on ports 8000 or 5173."
}
