param(
    [string]$PackageVersion = "0.7.0.0",
    [string]$OutputName = "Vinqelo Player 0.7.0 Store x64 - corregido.msix",
    [string]$SourceDirectory = "dist\Vinqelo Player Store Clean"
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$sourceApp = Join-Path $projectRoot $SourceDirectory
$staging = Join-Path $projectRoot "build\msix-staging-clean-$PackageVersion"
$verification = Join-Path $projectRoot "build\msix-verify-clean-$PackageVersion"
$output = Join-Path $projectRoot "dist\$OutputName"
$buildRoot = (Resolve-Path (Join-Path $projectRoot "build")).Path

function Reset-BuildDirectory {
    param([string]$Path)
    $absolute = [System.IO.Path]::GetFullPath($Path)
    if (-not $absolute.StartsWith($buildRoot + [System.IO.Path]::DirectorySeparatorChar)) {
        throw "La carpeta temporal quedó fuera de build: $absolute"
    }
    if (Test-Path -LiteralPath $absolute) {
        Remove-Item -LiteralPath $absolute -Recurse -Force
    }
    New-Item -ItemType Directory -Path $absolute -Force | Out-Null
}

function Test-PeFiles {
    param([string]$Root)
    $checked = 0
    $invalid = [System.Collections.Generic.List[string]]::new()
    Get-ChildItem -LiteralPath $Root -Recurse -File |
        Where-Object { $_.Extension -in ".exe", ".dll", ".pyd" } |
        ForEach-Object {
            $bytes = [System.IO.File]::ReadAllBytes($_.FullName)
            try {
                if ($bytes.Length -lt 256 -or $bytes[0] -ne 0x4D -or $bytes[1] -ne 0x5A) {
                    throw "encabezado MZ ausente"
                }
                $peOffset = [BitConverter]::ToInt32($bytes, 0x3C)
                if ($peOffset -lt 0 -or $peOffset + 160 -gt $bytes.Length) {
                    throw "desplazamiento PE inválido"
                }
                if ($bytes[$peOffset] -ne 0x50 -or $bytes[$peOffset + 1] -ne 0x45) {
                    throw "encabezado PE ausente"
                }
                $machine = [BitConverter]::ToUInt16($bytes, $peOffset + 4)
                if ($machine -ne 0x8664) {
                    throw ("arquitectura distinta de x64: 0x{0:X4}" -f $machine)
                }
                $optional = $peOffset + 24
                $magic = [BitConverter]::ToUInt16($bytes, $optional)
                $directoryBase = if ($magic -eq 0x20B) { 112 } elseif ($magic -eq 0x10B) { 96 } else { throw "cabecera opcional desconocida" }
                $securityEntry = $optional + $directoryBase + (4 * 8)
                $certificateOffset = [BitConverter]::ToUInt32($bytes, $securityEntry)
                $certificateSize = [BitConverter]::ToUInt32($bytes, $securityEntry + 4)
                if (($certificateOffset -eq 0) -xor ($certificateSize -eq 0)) {
                    throw "directorio de certificado incompleto"
                }
                if ($certificateOffset -gt 0 -and ([uint64]$certificateOffset + [uint64]$certificateSize) -gt [uint64]$bytes.Length) {
                    throw "certificado PE fuera del archivo"
                }
                $checked++
            }
            catch {
                $relative = [System.IO.Path]::GetRelativePath($Root, $_.FullName)
                $invalid.Add("$relative - $($_.Exception.Message)")
            }
        }
    if ($invalid.Count) {
        throw "Binarios PE inválidos:`n$($invalid -join "`n")"
    }
    return $checked
}

if (-not (Test-Path -LiteralPath $sourceApp -PathType Container)) {
    throw "No existe la compilación Store: $sourceApp"
}

Reset-BuildDirectory $staging
Copy-Item -Path (Join-Path $sourceApp "*") -Destination $staging -Recurse -Force

# PyInstaller incluyó Tk/Tcl aunque Vinqelo usa exclusivamente PySide6. Las dos
# DLL de la distribución de Python tienen un directorio Authenticode truncado,
# lo que hace fallar la firma de Microsoft Store con 0x800700C1.
$unneeded = @(
    (Join-Path $staging "_internal\tcl86t.dll"),
    (Join-Path $staging "_internal\tk86t.dll"),
    (Join-Path $staging "_internal\_tcl_data"),
    (Join-Path $staging "_internal\_tk_data")
)
foreach ($path in $unneeded) {
    if (Test-Path -LiteralPath $path) {
        Remove-Item -LiteralPath $path -Recurse -Force
    }
}

Copy-Item -LiteralPath (Join-Path $projectRoot "packaging\Assets") -Destination $staging -Recurse -Force
$manifestTemplate = Get-Content -LiteralPath (Join-Path $projectRoot "packaging\AppxManifest.xml") -Raw
$identityVersionPattern = '(<Identity\s+[^>]*\bVersion=")[^"]+(")'
$identityVersionReplacement = '${1}' + $PackageVersion + '${2}'
$manifest = [regex]::Replace(
    $manifestTemplate,
    $identityVersionPattern,
    $identityVersionReplacement,
    1
)
[System.IO.File]::WriteAllText(
    (Join-Path $staging "AppxManifest.xml"),
    $manifest,
    [System.Text.UTF8Encoding]::new($false)
)

$checkedBeforePack = Test-PeFiles $staging
$makeAppx = Get-ChildItem -LiteralPath (Join-Path $projectRoot "build\WindowsSdkBuildTools") -Recurse -File |
    Where-Object { $_.Name -eq "makeappx.exe" -and $_.FullName -match '\\x64\\' } |
    Select-Object -First 1 -ExpandProperty FullName
if (-not $makeAppx) {
    throw "No se encontró makeappx.exe x64."
}

if (Test-Path -LiteralPath $output) {
    Remove-Item -LiteralPath $output -Force
}
& $makeAppx pack /d $staging /p $output /o
if ($LASTEXITCODE -ne 0) { throw "MakeAppx no pudo crear el paquete." }

Reset-BuildDirectory $verification
& $makeAppx unpack /p $output /d $verification /o
if ($LASTEXITCODE -ne 0) { throw "MakeAppx no pudo verificar el paquete creado." }
$checkedAfterPack = Test-PeFiles $verification

[pscustomobject]@{
    Package = $output
    Version = $PackageVersion
    PeFilesBeforePack = $checkedBeforePack
    PeFilesAfterPack = $checkedAfterPack
    TClTkPresent = [bool](Get-ChildItem -LiteralPath $verification -Recurse -File | Where-Object { $_.Name -in "tcl86t.dll", "tk86t.dll" })
    Size = (Get-Item -LiteralPath $output).Length
}
