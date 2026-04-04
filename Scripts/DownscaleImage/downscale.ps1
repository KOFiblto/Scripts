param([string]$ImagePath, [int]$TargetMPArg)

$TargetMP = $TargetMPArg * 1000000

Add-Type -AssemblyName System.Drawing
$img = [System.Drawing.Image]::FromFile($ImagePath)
$currentMP = $img.Width * $img.Height

$scale = 1
if ($currentMP -gt $TargetMP) { 
    $scale = [math]::Sqrt($TargetMP / $currentMP)
}

$newW = [math]::Max(64, [math]::Round(($img.Width * $scale) / 64) * 64)
$newH = [math]::Max(64, [math]::Round(($img.Height * $scale) / 64) * 64)

if ($newW -eq $img.Width -and $newH -eq $img.Height) { 
    $img.Dispose()
    exit 
}

$newImg = New-Object System.Drawing.Bitmap($newW, $newH)
$g = [System.Drawing.Graphics]::FromImage($newImg)
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$g.DrawImage($img, 0, 0, $newW, $newH)
$g.Dispose()

$dir = [System.IO.Path]::GetDirectoryName($ImagePath)
$name = [System.IO.Path]::GetFileNameWithoutExtension($ImagePath)
$ext = [System.IO.Path]::GetExtension($ImagePath)

$subDir = Join-Path $dir "${TargetMPArg}MP"
if (-not (Test-Path $subDir)) {
    New-Item -ItemType Directory -Path $subDir | Out-Null
}
$newPath = Join-Path $subDir "${name}__${TargetMPArg}MP$ext"

if ($ext -match "(?i)\.jpe?g$") {
    $enc = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object MimeType -eq 'image/jpeg'
    $ep = New-Object System.Drawing.Imaging.EncoderParameters(1)
    $ep.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, [long]85)
    $newImg.Save($newPath, $enc, $ep)
} else {
    $newImg.Save($newPath, $img.RawFormat)
}

$newImg.Dispose()
$img.Dispose()