param(
    [string]$OutputDirectory = "store-assets\es-ES",
    [string]$DataDirectory = "store-assets\demo-library\data"
)

Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class VinqeloCaptureNative {
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left, Top, Right, Bottom; }
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int command);
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] public static extern void mouse_event(uint flags, uint dx, uint dy, uint data, UIntPtr extraInfo);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc callback, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
    public static IntPtr FindWindowForProcess(int processId) {
        IntPtr result = IntPtr.Zero;
        long largestArea = 0;
        EnumWindows(delegate(IntPtr hWnd, IntPtr lParam) {
            uint owner;
            GetWindowThreadProcessId(hWnd, out owner);
            if (owner == processId && IsWindowVisible(hWnd)) {
                RECT rect;
                if (GetWindowRect(hWnd, out rect)) {
                    long area = (long)(rect.Right - rect.Left) * (rect.Bottom - rect.Top);
                    if (area > largestArea) {
                        largestArea = area;
                        result = hWnd;
                    }
                }
            }
            return true;
        }, IntPtr.Zero);
        return result;
    }
    public static long WindowArea(IntPtr hWnd) {
        RECT rect;
        if (!GetWindowRect(hWnd, out rect)) return 0;
        return (long)(rect.Right - rect.Left) * (rect.Bottom - rect.Top);
    }
}
"@

function Save-WindowCapture {
    param([IntPtr]$Handle, [string]$Path)
    $rect = New-Object VinqeloCaptureNative+RECT
    [VinqeloCaptureNative]::GetWindowRect($Handle, [ref]$rect) | Out-Null
    $width = $rect.Right - $rect.Left
    $height = $rect.Bottom - $rect.Top
    $bitmap = New-Object System.Drawing.Bitmap($width, $height)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.CopyFromScreen($rect.Left, $rect.Top, 0, 0, $bitmap.Size)
    $bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    $graphics.Dispose()
    $bitmap.Dispose()
}

function Click-WindowPoint {
    param([IntPtr]$Handle, [int]$X, [int]$Y)
    $rect = New-Object VinqeloCaptureNative+RECT
    [VinqeloCaptureNative]::GetWindowRect($Handle, [ref]$rect) | Out-Null
    [VinqeloCaptureNative]::SetCursorPos($rect.Left + $X, $rect.Top + $Y) | Out-Null
    [VinqeloCaptureNative]::mouse_event(0x0002, 0, 0, 0, [UIntPtr]::Zero)
    [VinqeloCaptureNative]::mouse_event(0x0004, 0, 0, 0, [UIntPtr]::Zero)
}

$output = Join-Path (Get-Location) $OutputDirectory
New-Item -ItemType Directory -Path $output -Force | Out-Null
$previousDataDirectory = $env:VINQELO_DATA_DIR
$env:VINQELO_DATA_DIR = (Resolve-Path $DataDirectory).Path
$settingsPath = "HKCU:\Software\Vinqelo\Vinqelo Player\interface"
$hadLanguage = Test-Path $settingsPath
$previousLanguage = $null
if ($hadLanguage) {
    $previousLanguage = Get-ItemPropertyValue -Path $settingsPath -Name "language" -ErrorAction SilentlyContinue
}
New-Item -Path $settingsPath -Force | Out-Null
Set-ItemProperty -Path $settingsPath -Name "language" -Value "es"
$process = Start-Process -FilePath ".\.venv\Scripts\pythonw.exe" -ArgumentList "main.py" -WorkingDirectory (Get-Location) -PassThru
$appProcess = $null
try {
    $handle = [IntPtr]::Zero
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        Start-Sleep -Milliseconds 500
        $process.Refresh()
        $appProcess = Get-Process -Name "pythonw" -ErrorAction SilentlyContinue |
            Where-Object { $_.MainWindowTitle -like "Vinqelo Player*" } |
            Sort-Object StartTime -Descending |
            Select-Object -First 1
        $candidate = if ($null -ne $appProcess) {
            [VinqeloCaptureNative]::FindWindowForProcess($appProcess.Id)
        }
        else {
            [VinqeloCaptureNative]::FindWindowForProcess($process.Id)
        }
        if ($candidate -ne [IntPtr]::Zero -and [VinqeloCaptureNative]::WindowArea($candidate) -gt 500000) {
            $handle = $candidate
            break
        }
    }
    if ($handle -eq [IntPtr]::Zero) { throw "No se encontro la ventana de Vinqelo Player." }

    [VinqeloCaptureNative]::ShowWindow($handle, 3) | Out-Null
    [VinqeloCaptureNative]::SetForegroundWindow($handle) | Out-Null
    Start-Sleep -Seconds 3

    Click-WindowPoint $handle 100 132
    Start-Sleep -Seconds 8
    Save-WindowCapture $handle (Join-Path $output "01-biblioteca.png")

    Click-WindowPoint $handle 100 210
    Start-Sleep -Seconds 6
    Save-WindowCapture $handle (Join-Path $output "02-artistas.png")

    Click-WindowPoint $handle 100 249
    Start-Sleep -Seconds 6
    Save-WindowCapture $handle (Join-Path $output "03-albumes.png")

    Click-WindowPoint $handle 100 328
    Start-Sleep -Seconds 6
    Click-WindowPoint $handle 340 185
    Start-Sleep -Milliseconds 150
    Click-WindowPoint $handle 340 185
    Start-Sleep -Seconds 3
    Save-WindowCapture $handle (Join-Path $output "04-carpetas.png")
}
finally {
    if ($null -ne $appProcess -and -not $appProcess.HasExited) {
        Stop-Process -Id $appProcess.Id -Force
    }
    if (-not $process.HasExited) { Stop-Process -Id $process.Id -Force }
    if ($null -ne $previousLanguage) {
        Set-ItemProperty -Path $settingsPath -Name "language" -Value $previousLanguage
    }
    else {
        Remove-ItemProperty -Path $settingsPath -Name "language" -ErrorAction SilentlyContinue
        if (-not $hadLanguage) { Remove-Item -Path $settingsPath -ErrorAction SilentlyContinue }
    }
    $env:VINQELO_DATA_DIR = $previousDataDirectory
}
