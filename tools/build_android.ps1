param(
    [string]$Jdk = $env:JAVA_HOME,
    [string]$Sdk = $env:ANDROID_HOME,
    [string]$Python = "",
    [switch]$Checks
)
$ErrorActionPreference = 'Stop'
$lunaRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
if (-not $Python) { $Python = Join-Path $lunaRoot '.venv/Scripts/python.exe' }
if (-not $Jdk -or -not (Test-Path -LiteralPath (Join-Path $Jdk 'bin/java.exe'))) {
    throw 'JDK 17 absent. Fournir -Jdk ou JAVA_HOME.'
}
if (-not $Sdk -or -not (Test-Path -LiteralPath (Join-Path $Sdk 'platforms/android-36/android.jar'))) {
    throw 'SDK Android 36 absent. Fournir -Sdk ou ANDROID_HOME.'
}
if (-not (Test-Path -LiteralPath $Python)) { throw 'Python 3.13 absent. Fournir -Python.' }
$env:JAVA_HOME = $Jdk
$env:ANDROID_HOME = $Sdk
$lunaTasks = @('assembleDebug')
if ($Checks) { $lunaTasks += @('testDebugUnitTest', 'lintDebug') }
$lunaProject = Join-Path $lunaRoot 'android'
& (Join-Path $lunaProject 'gradlew.bat') -p $lunaProject @lunaTasks "-PbuildPython=$Python" --console=plain
if ($LASTEXITCODE -ne 0) { throw "Gradle a échoué : code $LASTEXITCODE" }
$lunaDist = Join-Path $lunaRoot 'dist'
New-Item -ItemType Directory -Path $lunaDist -Force | Out-Null
$lunaApk = Join-Path $lunaDist 'Luna-Android.apk'
Copy-Item -LiteralPath (Join-Path $lunaProject 'app/build/outputs/apk/debug/app-debug.apk') -Destination $lunaApk -Force
$lunaHash = (Get-FileHash -LiteralPath $lunaApk -Algorithm SHA256).Hash.ToLowerInvariant()
[System.IO.File]::WriteAllText((Join-Path $lunaDist 'Luna-Android.apk.sha256'), "$lunaHash  Luna-Android.apk`n", (New-Object System.Text.UTF8Encoding($false)))
Write-Output "APK : $lunaApk"
Write-Output "SHA256 : $lunaHash"
