# Minimal static server for previewing docs/ locally (Windows, no Python needed).
#   powershell -ExecutionPolicy Bypass -File scripts/serve-docs.ps1 [-Port 8787] [-Root docs]
param([int]$Port = 8787, [string]$Root = "docs")
$rootPath = (Resolve-Path (Join-Path $PSScriptRoot "..\$Root")).Path
$types = @{ ".html"="text/html; charset=utf-8"; ".json"="application/json"; ".xml"="application/rss+xml"; ".png"="image/png";
            ".mp3"="audio/mpeg"; ".js"="text/javascript"; ".css"="text/css"; ".ppn"="application/octet-stream"; ".pv"="application/octet-stream" }
$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://localhost:$Port/")
$listener.Start()
Write-Host "Serving $rootPath at http://localhost:$Port/"
while ($listener.IsListening) {
  $ctx = $listener.GetContext()
  $rel = [Uri]::UnescapeDataString($ctx.Request.Url.AbsolutePath.TrimStart('/'))
  if ($rel -eq "") { $rel = "index.html" }
  $file = Join-Path $rootPath $rel
  $res = $ctx.Response
  $res.Headers.Add("Access-Control-Allow-Origin", "*")
  if ((Test-Path $file -PathType Leaf) -and $file.StartsWith($rootPath)) {
    $bytes = [IO.File]::ReadAllBytes($file)
    $ext = [IO.Path]::GetExtension($file).ToLower()
    $res.ContentType = if ($types.ContainsKey($ext)) { $types[$ext] } else { "application/octet-stream" }
    $res.ContentLength64 = $bytes.Length
    $res.OutputStream.Write($bytes, 0, $bytes.Length)
  } else {
    $res.StatusCode = 404
  }
  $res.OutputStream.Close()
}
