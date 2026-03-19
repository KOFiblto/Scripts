param([string]$ImagePath, [string]$TargetArg)

$div64 = $TargetArg.EndsWith("_64")
$TargetMP = [int]($TargetArg -replace "_64", "") * 1000000

Add-Type -AssemblyName System.Drawing
$img = [System.Drawing.Image]::FromFile($ImagePath)
$currentMP = $img.Width * $img.Height

if ($currentMP -le $TargetMP -and -not $div64) { 
    $img.Dispose()
    exit 
}

$scale = [math]::Sqrt($TargetMP / $currentMP)
$newW = [int]($img.Width * $scale)
$newH = [int]($img.Height * $scale)

if ($div64) {
    $newW = [math]::Max(64, [math]::Round($newW / 64) * 64)
    $newH = [math]::Max(64, [math]::Round($newH / 64) * 64)
}

$newImg = New-Object System.Drawing.Bitmap($newW, $newH)
$g = [System.Drawing.Graphics]::FromImage($newImg)
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$g.DrawImage($img, 0, 0, $newW, $newH)
$g.Dispose()
$img.Dispose()

$dir = [System.IO.Path]::GetDirectoryName($ImagePath)
$name = [System.IO.Path]::GetFileNameWithoutExtension($ImagePath)
$ext = [System.IO.Path]::GetExtension($ImagePath)
$suffix = if ($div64) { "MP_div64" } else { "MP" }
$mpLabel = $TargetMP / 1000000

$newImg.Save((Join-Path $dir "${name}_${mpLabel}${suffix}${ext}"))
$newImg.Dispose()