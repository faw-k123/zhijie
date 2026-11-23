param(
    [string]$SourceRoot = 'D:\评论',
    [string]$DestinationRoot = (Join-Path $PSScriptRoot '..\media\audio'),
    [string]$ReportPath = (Join-Path $PSScriptRoot '..\..\design\audio-sync-report.json')
)

$ErrorActionPreference = 'Stop'
$audioExtensions = @('.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma')
$sourceAliases = @{
    'audio/民歌/东北民歌/大东北我的家乡.mp3' = '民歌\东北民歌\其他\大东北我的家乡 (DJ 版)\大东北我的家乡 (DJ 版).mp3'
    'audio/民歌/中原民歌/花木兰.mp3' = '民歌\中原民歌\其他\花木兰 (唱段)\花木兰.mp3'
    'audio/民歌/中原民歌/大河南我的家乡.mp3' = '民歌\中原民歌\其他\大河南是我的家乡\大河南是我的家乡.mp3'
    'audio/乐器/马头琴/天边.mp3' = '乐器\马头琴\其他\天邊\music_1863415461.mp3'
    'audio/乐器/唢呐/百鸟朝凤.mp3' = '乐器\唢呐\其他\百鳥朝鳳 (嗩吶獨奏)\music_445238141.mp3'
    'audio/说唱/上海说唱/升明日.mp3' = '说唱\上海说唱\其他\升明月-双档\升明月-双档 - 双档.mp3'
    'audio/戏曲/京剧/智斗.mp3' = '戏曲\京剧\其他\智斗(《沙家浜》)\music_5266411.mp3'
    'audio/戏曲/京剧/白素贞唱段.mp3' = '戏曲\京剧\其他\白素贞唱段(西皮垛板)\music_331512.mp3'
    'audio/戏曲/昆曲/牡丹亭游园惊梦.mp3' = '戏曲\昆曲\其他\昆曲《牡丹亭－游园惊梦》\music_1474589801.mp3'
    'audio/戏曲/昆曲/皂罗袍.mp3' = '戏曲\昆曲\其他\牡丹亭.游园---皂罗袍\music_292644.mp3'
    'audio/戏曲/昆曲/长生殿惊变.mp3' = '戏曲\昆曲\其他\长生殿·惊变·泣颜回\music_28234711.mp3'
    'audio/戏曲/评剧/打龙袍.mp3' = '戏曲\评剧\其他\打龙袍 (二)\music_28075175.mp3'
    'audio/戏曲/评剧/报花名.mp3' = '戏曲\评剧\其他\花为媒-报花名(评剧)\music_253535.mp3'
    'audio/戏曲/评剧/秦香莲.mp3' = '戏曲\评剧\其他\评剧-秦香莲\music_5266392.mp3'
    'audio/戏曲/秦腔/华阴老腔.mp3' = '戏曲\秦腔\其他\华阴老腔一声喊 (Live)\music_406072372.mp3'
    'audio/戏曲/秦腔/铡美案.mp3' = '戏曲\秦腔\其他\秦腔《铡美案》\music_1500216024.mp3'
    'audio/戏曲/豫剧/花木兰.mp3' = '戏曲\豫剧\其他\豫剧-花木兰\music_5266394.mp3'
    'audio/戏曲/豫剧/穆桂英挂帅.mp3' = '戏曲\豫剧\其他\豫剧-穆桂英挂帅\music_5266395.mp3'
    'audio/戏曲/越剧/天下掉下个林妹妹.mp3' = '戏曲\越剧\其他\红楼梦.天上掉下个林妹妹\music_305739.mp3'
    'audio/戏曲/越剧/西厢记.mp3' = '戏曲\越剧\其他\西厢记.琴心\music_5263663.mp3'
}

function Normalize-Name([string]$Value) {
    if ([string]::IsNullOrWhiteSpace($Value)) { return '' }
    return (($Value.Normalize([Text.NormalizationForm]::FormKC) -replace '[\s\p{P}\p{S}]', '').ToLowerInvariant())
}

function Get-AudioFiles([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) { return @() }
    return @(Get-ChildItem -LiteralPath $Path -File -Recurse | Where-Object {
        $audioExtensions -contains $_.Extension.ToLowerInvariant()
    })
}

function Test-AudioFile([IO.FileInfo]$File) {
    if (-not $File -or -not $File.Exists -or $File.Length -lt 12) { return $false }

    $stream = [IO.File]::OpenRead($File.FullName)
    try {
        $buffer = [byte[]]::new([Math]::Min(4096, [int]$File.Length))
        $read = $stream.Read($buffer, 0, $buffer.Length)
    }
    finally {
        $stream.Dispose()
    }

    if ($read -ge 5) {
        $prefix = [Text.Encoding]::ASCII.GetString($buffer, 0, [Math]::Min($read, 32)).TrimStart()
        if ($prefix.StartsWith('<!DOCTYPE', [StringComparison]::OrdinalIgnoreCase) -or
            $prefix.StartsWith('<html', [StringComparison]::OrdinalIgnoreCase)) {
            return $false
        }
    }

    $extension = $File.Extension.ToLowerInvariant()
    switch ($extension) {
        '.mp3' {
            if ($read -ge 3 -and $buffer[0] -eq 0x49 -and $buffer[1] -eq 0x44 -and $buffer[2] -eq 0x33) { return $true }
            for ($i = 0; $i -lt ($read - 1); $i++) {
                if ($buffer[$i] -eq 0xFF -and (($buffer[$i + 1] -band 0xE0) -eq 0xE0)) { return $true }
            }
            return $false
        }
        '.wav' { return $read -ge 12 -and [Text.Encoding]::ASCII.GetString($buffer, 0, 4) -eq 'RIFF' -and [Text.Encoding]::ASCII.GetString($buffer, 8, 4) -eq 'WAVE' }
        '.flac' { return $read -ge 4 -and [Text.Encoding]::ASCII.GetString($buffer, 0, 4) -eq 'fLaC' }
        '.ogg' { return $read -ge 4 -and [Text.Encoding]::ASCII.GetString($buffer, 0, 4) -eq 'OggS' }
        { $_ -in @('.m4a', '.aac') } {
            return ($read -ge 8 -and [Text.Encoding]::ASCII.GetString($buffer, 4, 4) -eq 'ftyp') -or
                ($buffer[0] -eq 0xFF -and (($buffer[1] -band 0xF0) -eq 0xF0))
        }
        '.wma' { return $read -ge 4 -and $buffer[0] -eq 0x30 -and $buffer[1] -eq 0x26 -and $buffer[2] -eq 0xB2 -and $buffer[3] -eq 0x75 }
        default { return $false }
    }
}

$connectionString = 'Driver={ODBC Driver 18 for SQL Server};Server=localhost;Database=music_db_test;Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;'
$connection = [System.Data.Odbc.OdbcConnection]::new($connectionString)
$records = [System.Collections.Generic.List[object]]::new()
try {
    $connection.Open()
    $command = $connection.CreateCommand()
    $command.CommandText = "SELECT id, title, audio_url FROM dbo.traditional_song WHERE audio_url LIKE 'audio/%' ORDER BY id"
    $reader = $command.ExecuteReader()
    while ($reader.Read()) {
        $records.Add([pscustomobject]@{
            id = [int]$reader['id']
            title = [string]$reader['title']
            audio_url = [string]$reader['audio_url']
        })
    }
    $reader.Close()
}
finally {
    $connection.Close()
}

$sourceFiles = Get-AudioFiles $SourceRoot
$copied = [System.Collections.Generic.List[object]]::new()
$missing = [System.Collections.Generic.List[object]]::new()
$ambiguous = [System.Collections.Generic.List[object]]::new()
$invalid = [System.Collections.Generic.List[object]]::new()

foreach ($record in $records) {
    $url = $record.audio_url.Replace('\', '/')
    if (-not $url.StartsWith('audio/', [StringComparison]::OrdinalIgnoreCase)) { continue }

    $relativePath = $url.Substring(6)
    $segments = @($relativePath -split '/')
    if ($segments.Count -lt 2 -or $segments -contains '..') {
        $missing.Add([pscustomobject]@{ id = $record.id; title = $record.title; audio_url = $url; reason = 'invalid_path' })
        continue
    }

    $target = Join-Path $DestinationRoot ($segments -join [IO.Path]::DirectorySeparatorChar)
    $directSource = Join-Path $SourceRoot ($segments -join [IO.Path]::DirectorySeparatorChar)
    $desiredStem = [IO.Path]::GetFileNameWithoutExtension($segments[-1])
    $categorySegments = if ($segments.Count -gt 1) { $segments[0..($segments.Count - 2)] } else { @() }
    $sourceCategoryRoot = Join-Path $SourceRoot ($categorySegments -join [IO.Path]::DirectorySeparatorChar)

    $candidates = @()
    if ($sourceAliases.ContainsKey($url)) {
        $aliasSource = Join-Path $SourceRoot $sourceAliases[$url]
        if (Test-Path -LiteralPath $aliasSource -PathType Leaf) {
            $candidates = @((Get-Item -LiteralPath $aliasSource))
        }
    }
    elseif (Test-Path -LiteralPath $directSource -PathType Leaf) {
        $candidates = @((Get-Item -LiteralPath $directSource))
    }
    else {
        $categoryFiles = Get-AudioFiles $sourceCategoryRoot
        $exactParent = @($categoryFiles | Where-Object { $_.Directory.Name -ieq $desiredStem })
        $exactFile = @($categoryFiles | Where-Object { $_.BaseName -ieq $desiredStem })
        if ($exactParent.Count -gt 0) { $candidates = $exactParent }
        elseif ($exactFile.Count -gt 0) { $candidates = $exactFile }
        else {
            $normalizedStem = Normalize-Name $desiredStem
            $normalizedParent = @($categoryFiles | Where-Object { (Normalize-Name $_.Directory.Name) -eq $normalizedStem })
            $normalizedFile = @($categoryFiles | Where-Object { (Normalize-Name $_.BaseName) -eq $normalizedStem })
            if ($normalizedParent.Count -gt 0) { $candidates = $normalizedParent }
            elseif ($normalizedFile.Count -gt 0) { $candidates = $normalizedFile }
        }
    }

    $invalidCandidates = @($candidates | Where-Object { -not (Test-AudioFile $_) })
    $candidates = @($candidates | Where-Object { Test-AudioFile $_ })

    if ($candidates.Count -eq 0) {
        if ($invalidCandidates.Count -gt 0) {
            $invalid.Add([pscustomobject]@{
                id = $record.id
                title = $record.title
                audio_url = $url
                sources = @($invalidCandidates.FullName)
                reason = 'source_is_not_audio'
            })
            continue
        }
        $missing.Add([pscustomobject]@{ id = $record.id; title = $record.title; audio_url = $url; reason = 'not_found' })
        continue
    }
    if ($candidates.Count -gt 1) {
        $ambiguous.Add([pscustomobject]@{ id = $record.id; title = $record.title; audio_url = $url; candidates = @($candidates.FullName) })
        continue
    }

    $targetDirectory = Split-Path -Parent $target
    New-Item -ItemType Directory -Path $targetDirectory -Force | Out-Null
    Copy-Item -LiteralPath $candidates[0].FullName -Destination $target -Force
    $copied.Add([pscustomobject]@{
        id = $record.id
        title = $record.title
        audio_url = $url
        source = $candidates[0].FullName
        destination = $target
        bytes = (Get-Item -LiteralPath $target).Length
    })
}

$report = [ordered]@{
    generated_at = (Get-Date).ToString('s')
    database = 'music_db_test'
    queried = $records.Count
    copied = $copied.Count
    missing = $missing.Count
    ambiguous = $ambiguous.Count
    invalid = $invalid.Count
    copied_files = $copied
    missing_files = $missing
    ambiguous_files = $ambiguous
    invalid_files = $invalid
}
$reportDirectory = Split-Path -Parent $ReportPath
New-Item -ItemType Directory -Path $reportDirectory -Force | Out-Null
$report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $ReportPath -Encoding utf8

[pscustomobject]@{
    DatabaseRows = $records.Count
    Copied = $copied.Count
    Missing = $missing.Count
    Ambiguous = $ambiguous.Count
    Invalid = $invalid.Count
    Destination = (Resolve-Path -LiteralPath $DestinationRoot).Path
    Report = (Resolve-Path -LiteralPath $ReportPath).Path
} | Format-List
