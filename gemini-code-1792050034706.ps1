$baseUrl = "http://localhost:8000"

Write-Host "Registering original: 15Seconds-DEMO.mp4..." -ForegroundColor Cyan
$regRaw = curl.exe -s -X POST "$baseUrl/register" -F "file=@15Seconds-DEMO.mp4"
$reg = $regRaw | ConvertFrom-Json
Write-Host "Registered successfully! Record ID: $($reg.record_id)`n" -ForegroundColor Green

$testFiles = @(
    "15Seconds-DEMO.mp4",
    "test_transcode.mp4",
    "test_resolution.mp4",
    "test_trim.mp4",
    "test_splice.mp4",
    "test_speed.mp4",
    "test_watermark.mp4",
    "test_colorgrade.mp4",
    "test_crop_reframe.mp4",
    "test_censor_blur.mp4",
    "test_freeze.mp4",
    "test_audio_swap.mp4"
)

$results = foreach ($file in $testFiles) {
    if (Test-Path $file) {
        try {
            $rawJson = curl.exe -s -X POST "$baseUrl/verify" -F "file=@$file"
            $res = $rawJson | ConvertFrom-Json

            [PSCustomObject]@{
                File        = $file
                ExactMatch  = $res.exact_match
                Authentic   = $res.is_authentic
                Similarity  = "$($res.overall_similarity)%"
                VisualAlt   = $res.alterations.visually_altered.detected
                TimeAlt     = $res.alterations.time_altered.detected
                QualityAlt  = $res.alterations.quality_altered.detected
                Segments    = if ($res.alterations.visually_altered.segments) { 
                                ($res.alterations.visually_altered.segments | ForEach-Object { "$($_.start)-$($_.end)" }) -join ", " 
                              } else { "-" }
            }
        } catch {
            [PSCustomObject]@{
                File        = $file
                ExactMatch  = "ERR"
                Authentic   = "ERR"
                Similarity  = "ERR"
                VisualAlt   = "ERR"
                TimeAlt     = "ERR"
                QualityAlt  = "ERR"
                Segments    = $_.Exception.Message
            }
        }
    }
}

$results | Format-Table -AutoSize