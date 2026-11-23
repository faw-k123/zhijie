param([Parameter(Mandatory = $true)][string]$FrontendRoot)

$node = (Get-Command node.exe).Source
$process = Start-Process -FilePath $node -ArgumentList @('.\node_modules\vite\bin\vite.js', '--configLoader', 'runner', '--host', '127.0.0.1', '--port', '5177', '--strictPort') -WorkingDirectory $FrontendRoot -PassThru
Start-Sleep -Seconds 8
$process.Refresh()
Write-Output "Id=$($process.Id) HasExited=$($process.HasExited) ExitCode=$(if ($process.HasExited) { $process.ExitCode } else { 'running' })"
