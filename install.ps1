# ai-job-search-kr 설치 스크립트 (Windows PowerShell)
#
#   powershell -ExecutionPolicy Bypass -File install.ps1
#   powershell -ExecutionPolicy Bypass -File install.ps1 -Check   # 상태만 본다
#
# 확인·설치하는 것: git, Python 3.10+, Bun, pandoc, Chrome, PDF 검사용 파이썬 패키지,
# 포털 검색 CLI 의존성, 프로필 파일, 그리고 Claude Code 또는 Codex CLI 중 하나.
# 윈도우에서는 git 이 심볼릭 링크를 텍스트 파일로 받는 경우가 있어 그것도 복구한다.
param([switch]$Check)

$ErrorActionPreference = 'Continue'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
$script:Ok = 0
$script:Missing = 0

function Write-Ok   ($m) { Write-Host "  [OK]   $m";   $script:Ok++ }
function Write-Miss ($m) { Write-Host "  [없음] $m";   $script:Missing++ }
function Write-Info ($m) { Write-Host "  ...    $m" }
function Have ($name) { return [bool](Get-Command $name -ErrorAction SilentlyContinue) }

function Install-With-Winget ($id, $label, $hint) {
    if ($Check) { Write-Miss "$label ($hint)"; return }
    if (Have 'winget') {
        Write-Info "winget install $id"
        winget install --id $id -e --accept-source-agreements --accept-package-agreements | Out-Null
        if ($LASTEXITCODE -eq 0) { Write-Ok "$label 설치" } else { Write-Miss "$label 설치 실패. $hint" }
    } else {
        Write-Miss "$label. $hint"
    }
}

Write-Host "== 1. 기본 도구"
if (Have 'git') { Write-Ok 'git' } else { Install-With-Winget 'Git.Git' 'git' 'https://git-scm.com' }

$Py = $null
foreach ($c in @('python', 'python3', 'py')) {
    if (Have $c) {
        $v = & $c -c "import sys; print('%d.%d' % sys.version_info[:2]); sys.exit(0 if sys.version_info >= (3,10) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) { $Py = $c; Write-Ok "Python $v"; break }
    }
}
if (-not $Py) { Install-With-Winget 'Python.Python.3.12' 'Python 3.10 이상' 'https://www.python.org/downloads' }

if (Have 'bun') {
    Write-Ok "Bun $(bun --version)"
} elseif ($Check) {
    Write-Miss 'Bun (https://bun.sh)'
} else {
    Write-Info 'Bun 설치 (https://bun.sh)'
    try {
        Invoke-RestMethod https://bun.sh/install.ps1 | Invoke-Expression
        $env:Path = "$env:USERPROFILE\.bun\bin;$env:Path"
        if (Have 'bun') { Write-Ok 'Bun 설치' } else { Write-Miss 'Bun 설치 실패. https://bun.sh' }
    } catch { Write-Miss 'Bun 설치 실패. https://bun.sh' }
}

Write-Host "== 2. PDF 생성"
if (Have 'pandoc') { Write-Ok 'pandoc' } else { Install-With-Winget 'JohnMacFarlane.Pandoc' 'pandoc' 'https://pandoc.org/installing.html' }

$ChromePaths = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe"
)
$Chrome = $env:CHROME_BIN
if (-not ($Chrome -and (Test-Path $Chrome))) { $Chrome = $ChromePaths | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1 }
if ($Chrome) { Write-Ok "Chrome ($Chrome)" }
else { Write-Miss 'Chrome. https://www.google.com/chrome 설치 후 경로가 다르면 CHROME_BIN 환경변수로 지정' }

Write-Host "== 3. 파이썬 패키지 (.venv)"
$VenvPy = Join-Path $Root '.venv\Scripts\python.exe'
if ($Py) {
    if ($Check) {
        if ((Test-Path $VenvPy) -and (& $VenvPy -c 'import pypdf' 2>$null; $LASTEXITCODE -eq 0)) { Write-Ok '.venv + pypdf' }
        else { Write-Miss '.venv (install.ps1 로 생성)' }
    } else {
        if (-not (Test-Path $VenvPy)) { & $Py -m venv .venv | Out-Null }
        & $VenvPy -m pip install -q --upgrade pip 2>$null | Out-Null
        & $VenvPy -m pip install -q pypdf pytest 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { Write-Ok '.venv + pypdf + pytest' } else { Write-Miss 'pypdf 설치 실패. PDF 검사는 건너뛴다' }
    }
}

Write-Host "== 4. 포털 검색 도구"
foreach ($dir in Get-ChildItem -Path '.agents\skills' -Directory -Filter '*-search' -ErrorAction SilentlyContinue) {
    $cli = Join-Path $dir.FullName 'cli'
    if (-not (Test-Path (Join-Path $cli 'package.json'))) { continue }
    if ($Check) {
        if (Test-Path (Join-Path $cli 'node_modules')) { Write-Ok $dir.Name } else { Write-Miss "$($dir.Name) (bun install 필요)" }
    } elseif (Have 'bun') {
        Push-Location $cli; bun install --silent 2>$null | Out-Null; Pop-Location
        if ($LASTEXITCODE -eq 0) { Write-Ok $dir.Name } else { Write-Miss "$($dir.Name) bun install 실패" }
    } else {
        Write-Miss "$($dir.Name) (Bun 없음)"
    }
}

Write-Host "== 4.5 프로필 파일"
$Profiles = @(
    '.agents\skills\job-application-assistant\01-candidate-profile',
    '.agents\skills\job-application-assistant\03-glossary',
    '.agents\skills\job-application-assistant\05-profiles',
    '.agents\skills\job-scraper\search-config'
)
foreach ($t in $Profiles) {
    $real = "$t.md"; $tpl = "$t.template.md"; $name = Split-Path $real -Leaf
    if (Test-Path $real) { Write-Ok "$name (있음)" }
    elseif ($Check) { Write-Miss "$name (install.ps1 이 템플릿에서 만든다)" }
    else { Copy-Item $tpl $real; Write-Ok "$name 템플릿에서 생성" }
}

Write-Host "== 4.7 스킬 링크"
# 윈도우에서 core.symlinks 가 꺼진 채로 clone 하면 링크가 대상 경로를 담은 텍스트 파일이 된다.
# 디렉토리 정션으로 바꾼다. 정션은 관리자 권한이 필요 없다.
$LinkDir = Join-Path $Root '.claude\skills'
$Broken = 0; $Fixed = 0; $Good = 0
if (Test-Path $LinkDir) {
    foreach ($entry in Get-ChildItem $LinkDir -Force) {
        $target = Join-Path $Root ".agents\skills\$($entry.Name)"
        $isLink = $entry.Attributes -band [IO.FileAttributes]::ReparsePoint
        if ($isLink -and (Test-Path (Join-Path $entry.FullName 'SKILL.md'))) { $Good++; continue }
        if ($entry.PSIsContainer -and (Test-Path (Join-Path $entry.FullName 'SKILL.md'))) { $Good++; continue }
        $Broken++
        if ($Check) { continue }
        if (-not (Test-Path $target)) { Write-Miss "$($entry.Name): 원본 $target 이 없다"; continue }
        Remove-Item $entry.FullName -Force -Recurse -ErrorAction SilentlyContinue
        New-Item -ItemType Junction -Path $entry.FullName -Target $target -ErrorAction SilentlyContinue | Out-Null
        if (Test-Path (Join-Path $entry.FullName 'SKILL.md')) { $Fixed++ } else { Write-Miss "$($entry.Name): 링크 복구 실패" }
    }
}
if ($Broken -eq 0) { Write-Ok "스킬 링크 $Good 개 정상" }
elseif ($Check) { Write-Miss "스킬 링크 $Broken 개가 깨졌다 (install.ps1 실행으로 복구)" }
elseif ($Fixed -eq $Broken) { Write-Ok "스킬 링크 $Fixed 개 복구, $Good 개 정상" }

Write-Host "== 5. 에이전트"
if (Have 'claude') { Write-Ok 'Claude Code' } else { Write-Miss 'Claude Code. https://claude.com/claude-code (둘 중 하나면 된다)' }
if (Have 'codex')  { Write-Ok 'Codex CLI' }   else { Write-Miss 'Codex CLI. https://developers.openai.com/codex (둘 중 하나면 된다)' }

Write-Host "== 6. 동작 확인"
if ((Have 'bun') -and (Test-Path '.agents\skills\wanted-search\cli\node_modules')) {
    bun run .agents\skills\wanted-search\cli\src\cli.ts search -q "백엔드 개발자" --limit 1 --format json 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { Write-Ok '원티드 검색 응답' } else { Write-Miss '원티드 검색 실패. 네트워크를 확인한다' }
}
if ($Py) {
    & $Py tools\check_codex_skills.py 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { Write-Ok '스킬 14개 인식' } else { Write-Miss '스킬 검사 실패. python tools\check_codex_skills.py 를 직접 돌려 본다' }
}

Write-Host ""
Write-Host "정상 $script:Ok, 없음 $script:Missing"
if ($script:Missing -gt 0) {
    Write-Host "위 [없음] 항목을 해결한 뒤 다시 실행한다. Claude Code 와 Codex 는 하나만 있으면 된다."
    exit 1
} else {
    Write-Host "준비 끝. 다음 순서:"
    Write-Host "  1) documents\resume\ 에 이력서 파일을 넣는다 (있으면 포트폴리오는 documents\portfolio\)"
    Write-Host "  2) claude 또는 codex 를 이 폴더에서 연다"
    Write-Host "  3) /setup (Codex 는 `$setup) 을 입력한다"
    exit 0
}
