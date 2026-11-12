# Polaris R001 - instalador/diagnostico unico. Windows PowerShell 5.1.
# Respeita outras ferramentas/projetos: nenhum reset de repo, nenhuma remocao ou alteracao de banco de dados.
[CmdletBinding()]
param(
    [ValidateSet('Menu','Check','Install','Prepare','Build','All','OtherProjects','EmulatorBaseline','EmulatorPatched','EmulatorDuo','EmulatorSmoke','TranslationCapture','EmulatorDisplay','EmulatorDisplayRestore')]
    [string]$Action='Menu',
    [string]$Workspace=(Join-Path $env:USERPROFILE 'PolarisDev'),
    [switch]$Yes
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
$script:Workspace=[IO.Path]::GetFullPath($Workspace)
$script:PolarisDir=Join-Path $script:Workspace 'Polaris'
$script:BuildWorkspace=Join-Path $script:Workspace 'PolarisLocal'
$script:ReportDir=Join-Path $script:Workspace 'relatorios'
$script:Branch='r001/multisource-foundation'
$script:Pin='0fb80c439ef816eeb50674f1b90af39918b176d8'
$script:Repo='https://github.com/Hailton-Reis/Polaris.git'
$script:RequiredSDK=@('platform-tools','platforms;android-37.0','build-tools;36.0.0','build-tools;37.0.0','ndk;29.0.14206865','ndk;28.2.13676358','cmake;3.22.1')
$script:Findings=New-Object System.Collections.ArrayList
$script:LogFile=$null
$script:JsonReport=$null
$script:HadMenuFailure=$false
$script:TranscriptFile=$null
$script:TranscriptStarted=$false
$script:WingetPackages=[ordered]@{
    'Git for Windows'='Git.Git'
    'Python 3'='Python.Python.3.13'
    'JDK 21 (Temurin)'='EclipseAdoptium.Temurin.21.JDK'
    'Android Studio'='Google.AndroidStudio'
}
function Say([string]$Text,[string]$Color='Gray') {
    Write-Host $Text -ForegroundColor $Color
    if($script:LogFile) { Add-Content -LiteralPath $script:LogFile -Value $Text -Encoding UTF8 }
}
function New-Session {
    [IO.Directory]::CreateDirectory($script:ReportDir) | Out-Null
    $id=(Get-Date).ToString('yyyyMMdd-HHmmss')+'-'+[Guid]::NewGuid().ToString('N').Substring(0,6)
    $script:LogFile=Join-Path $script:ReportDir ('polaris-'+$id+'.log')
    $script:JsonReport=Join-Path $script:ReportDir ('polaris-'+$id+'.json')
    $script:TranscriptFile=Join-Path $script:ReportDir ('polaris-'+$id+'.transcript.txt')
    try {
        Start-Transcript -LiteralPath $script:TranscriptFile -ErrorAction Stop | Out-Null
        $script:TranscriptStarted=$true
    } catch {
        Say ('[AVISO] Registro completo indisponivel: '+$_.Exception.Message) 'Yellow'
    }
    Say "Polaris R001 - CORRECAO 2026-10-23 - sessao $id" 'Cyan'
    if($script:TranscriptStarted){Say ('Transcricao completa: '+$script:TranscriptFile)}
    Say "Workspace: $script:Workspace"
}
function Found([string]$Name,[bool]$Present,[string]$Details,[bool]$Required=$true) {
    $status=if($Present){'OK'}elseif($Required){'FALTA'}else{'OPCIONAL'}
    $color=if($Present){'Green'}elseif($Required){'Yellow'}else{'DarkGray'}
    Say "[$status] $Name - $Details" $color
    [void]$script:Findings.Add([pscustomobject]@{name=$Name;status=$status;detail=$Details})
}
function CmdPath([string]$Name) {
    $cmd=Get-Command $Name -ErrorAction SilentlyContinue
    if($cmd){return $cmd.Source}
    return $null
}
function Refresh-Path {
    $machine=[Environment]::GetEnvironmentVariable('Path','Machine')
    $user=[Environment]::GetEnvironmentVariable('Path','User')
    $env:Path=@($machine,$user,$env:Path) -join ';'
}
function Find-Git {
    $x=CmdPath 'git.exe'
    if($x){return $x}
    foreach($root in @($env:ProgramFiles,${env:ProgramFiles(x86)},$env:LOCALAPPDATA)) {
        if(!$root){continue}
        foreach($p in @('Git\cmd\git.exe','Programs\Git\cmd\git.exe')){
            $candidate=Join-Path $root $p
            if(Test-Path -LiteralPath $candidate -PathType Leaf){return $candidate}
        }
    }
    return $null
}
function Find-Bash {
    $g=Find-Git
    $paths=@()
    if($g){$gitDir=Split-Path (Split-Path $g -Parent) -Parent; $paths+=Join-Path $gitDir 'bin\bash.exe'}
    foreach($root in @($env:ProgramFiles,${env:ProgramFiles(x86)},$env:LOCALAPPDATA)) {
        if(!$root){continue}
        $paths+=Join-Path $root 'Git\bin\bash.exe'
        $paths+=Join-Path $root 'Programs\Git\bin\bash.exe'
    }
    foreach($p in $paths){if(Test-Path -LiteralPath $p -PathType Leaf){return $p}}
    return $null
}
function Find-Python {
    $py=CmdPath 'py.exe'
    if($py){
        try{
            $v=(& $py -3 --version 2>&1 | Out-String)
            if($LASTEXITCODE -eq 0 -and $v -match 'Python 3\.(1[0-9]|[2-9][0-9])\.'){
                $exe=(& $py -3 -c 'import sys;print(sys.executable)' 2>$null | Select-Object -First 1)
                return [pscustomobject]@{exe=$exe;run=$py;args=@('-3');version=$v.Trim()}
            }
        }catch{}
    }
    $p=CmdPath 'python.exe'
    if($p){
        try{
            $v=(& $p --version 2>&1 | Out-String)
            if($LASTEXITCODE -eq 0 -and $v -match 'Python 3\.(1[0-9]|[2-9][0-9])\.'){
                return [pscustomobject]@{exe=$p;run=$p;args=@();version=$v.Trim()}
            }
        }catch{}
    }
    return $null
}
function Find-Jdk21 {
    $homes=@()
    if($env:JAVA_HOME){$homes+=$env:JAVA_HOME}
    foreach($root in @($env:ProgramFiles,$env:LOCALAPPDATA)){
        if(!$root){continue}
        foreach($dir in @('Eclipse Adoptium','Java','Microsoft','Programs\Eclipse Adoptium')){
            $base=Join-Path $root $dir
            if(Test-Path -LiteralPath $base -PathType Container){
                $homes+=@(Get-ChildItem -LiteralPath $base -Directory -ErrorAction SilentlyContinue | Where-Object {$_.Name -match '(?i)(jdk|temurin).?21|^21'} | ForEach-Object {$_.FullName})
            }
        }
    }
    # $HOME is a built-in read-only PowerShell variable (names are case-insensitive).
    # Never use $home as a loop variable; it fails once an installed JDK is discovered.
    foreach($jdkHome in ($homes | Select-Object -Unique)) {
        $java=Join-Path $jdkHome 'bin\java.exe'
        $javac=Join-Path $jdkHome 'bin\javac.exe'
        if(!(Test-Path -LiteralPath $java -PathType Leaf) -or !(Test-Path -LiteralPath $javac -PathType Leaf)){continue}
        try{ $ver=(& $java --version 2>$null | Out-String); if($ver -match '(?i)(openjdk|java) 21(?:\.|\s|$)'){return $jdkHome} }catch{}
    }
    return $null
}
function Find-AndroidStudio {
    $paths=@()
    foreach($root in @($env:ProgramFiles,${env:ProgramFiles(x86)},$env:LOCALAPPDATA)){
        if(!$root){continue}
        $paths+=Join-Path $root 'Android\Android Studio\bin\studio64.exe'
        $paths+=Join-Path $root 'Programs\Android Studio\bin\studio64.exe'
    }
    foreach($p in $paths){if(Test-Path -LiteralPath $p -PathType Leaf){return $p}}
    foreach($key in @('HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*','HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*')) {
        # StrictMode: not every Windows uninstall registry entry contains DisplayName or InstallLocation.
        # Read optional properties defensively; unrelated programs must never abort our preflight.
        $items=Get-ItemProperty -Path $key -ErrorAction SilentlyContinue | Where-Object {
            $display=$_.PSObject.Properties['DisplayName']
            $null -ne $display -and ([string]$display.Value -like 'Android Studio*')
        }
        foreach($entry in $items){
            $location=$entry.PSObject.Properties['InstallLocation']
            if($null -ne $location -and -not [string]::IsNullOrWhiteSpace([string]$location.Value)){
                $p=Join-Path ([string]$location.Value) 'bin\studio64.exe'
                if(Test-Path -LiteralPath $p -PathType Leaf){return $p}
            }
        }
    }
    return $null
}
function Find-Sdk {
    $paths=@($env:ANDROID_HOME,$env:ANDROID_SDK_ROOT)
    if($env:LOCALAPPDATA){$paths+=Join-Path $env:LOCALAPPDATA 'Android\Sdk'}
    foreach($p in $paths){if($p -and (Test-Path -LiteralPath $p -PathType Container)){return [IO.Path]::GetFullPath($p)}}
    if($env:LOCALAPPDATA){return Join-Path $env:LOCALAPPDATA 'Android\Sdk'}
    return $null
}
function Find-SdkManager([string]$Sdk){
    if(!$Sdk){return $null}
    $latest=Join-Path $Sdk 'cmdline-tools\latest\bin\sdkmanager.bat'
    if(Test-Path -LiteralPath $latest -PathType Leaf){return $latest}
    $dir=Join-Path $Sdk 'cmdline-tools'
    if(Test-Path -LiteralPath $dir -PathType Container){
        $all=Get-ChildItem -LiteralPath $dir -Recurse -Filter 'sdkmanager.bat' -File -ErrorAction SilentlyContinue | Select-Object -First 1
        if($all){return $all.FullName}
    }
    return $null
}
function Check-SdkPackage([string]$Sdk,[string]$Pkg) {
    $path=Join-Path $Sdk ($Pkg.Replace(';','\'))
    return (Test-Path -LiteralPath $path -PathType Container) -and (Test-Path -LiteralPath (Join-Path $path 'source.properties') -PathType Leaf)
}
function Get-Status {
    $script:Findings.Clear()
    Say ''
    Say '=== PRE-FLIGHT DAS FERRAMENTAS ===' 'Cyan'
    $wing=CmdPath 'winget.exe'; Found 'winget (instalador)' ([bool]$wing) $(if($wing){$wing}else{'Instale App Installer pela Microsoft Store'}) $false
    $git=Find-Git; Found 'Git' ([bool]$git) $(if($git){$git}else{'Necessario para clonar os repositorios'})
    $bash=Find-Bash;Found 'Git Bash' ([bool]$bash) $(if($bash){$bash}else{'Incluido no Git for Windows'})
    $py=Find-Python;Found 'Python 3.10+' ([bool]$py) $(if($py){$py.version}else{'Necessario para o orquestrador existente'})
    $jdk=Find-Jdk21;Found 'JDK 21' ([bool]$jdk) $(if($jdk){$jdk}else{'Temurin 21 + javac'})
    $studio=Find-AndroidStudio;Found 'Android Studio' ([bool]$studio) $(if($studio){$studio}else{'IDE Android oficial'})
    $sdk=Find-Sdk;Found 'Android SDK' ([bool]($sdk -and (Test-Path -LiteralPath $sdk -PathType Container))) $(if($sdk){$sdk}else{'Nao localizado'})
    if($sdk){
        $manager=Find-SdkManager $sdk
        Found 'SDK Command-line Tools' ([bool]$manager) $(if($manager){$manager}else{'Necessarias para instalacao automatizada de pacotes'})
        foreach($item in $script:RequiredSDK){Found ('SDK '+$item) (Check-SdkPackage $sdk $item) $(if((Check-SdkPackage $sdk $item)){'Instalado'}else{'Ausente'})}
    }
    $node=CmdPath 'node.exe';Found 'Node.js (Vai Quem Quer)' ([bool]$node) $(if($node){$node}else{'Opcional para o projeto web'}) $false
    $dotnet=CmdPath 'dotnet.exe';Found '.NET SDK (CameraGuard)' ([bool]$dotnet) $(if($dotnet){$dotnet}else{'Opcional; CameraGuard usa SDK 8.0.425 fixado'}) $false
    $adb=if($sdk){Join-Path $sdk 'platform-tools\adb.exe'}else{$null}
    Found 'ADB (dispositivo de testes)' ([bool]($adb -and (Test-Path -LiteralPath $adb))) $(if($adb){$adb}else{'Configurado pelo SDK Platform Tools'}) $false
    Say ''
    $missing=@($script:Findings | Where-Object {$_.status -eq 'FALTA'})
    Say ('Resumo: '+$missing.Count+' requisitos pendentes.')
    $data=[ordered]@{
        schema=1
        created_utc=[DateTime]::UtcNow.ToString('o')
        project='Polaris'
        scope='WINDOWS_ENV_PREFLIGHT_NOT_ANDROID_RUNTIME'
        status=if($missing.Count -eq 0){'READY_TO_ATTEMPT_BUILD'}else{'MISSING_REQUIREMENTS'}
        tools=@($script:Findings)
    }
    [IO.File]::WriteAllText($script:JsonReport,($data | ConvertTo-Json -Depth 5),(New-Object System.Text.UTF8Encoding($false)))
    Say ('Relatorio JSON: '+$script:JsonReport)
    return ($missing.Count -eq 0)
}
function Confirm-Action([string]$What){
    if($Yes){return $true}
    Write-Host "\nACAO: $What" -ForegroundColor Yellow
    $x=Read-Host 'Digite SIM para continuar (qualquer outra resposta cancela)'
    return $x -eq 'SIM'
}
function Install-WingetPackage([string]$Name,[string]$Id){
    $wing=CmdPath 'winget.exe'
    if(!$wing){throw 'winget nao encontrado. Instale App Installer pela Microsoft Store e abra novamente o CMD.'}
    Say "Instalando $Name ($Id) via winget..." 'Yellow'
    & $wing install --id $Id --exact --source winget --accept-package-agreements --accept-source-agreements --disable-interactivity
    if($LASTEXITCODE -ne 0){throw "Falha winget para ${Id}: $LASTEXITCODE. Resolva e execute novamente."}
    Refresh-Path
}
function Install-Tools {
    Say '=== INSTALACAO DE FERRAMENTAS AUSENTES ===' 'Cyan'
    if(!(Confirm-Action 'Instalar dependencias faltantes para o Polaris via winget e SDK Google?')){throw 'Instalacao cancelada pelo operador.'}
    $present=@{'Git for Windows'=[bool](Find-Git);'Python 3'=[bool](Find-Python);'JDK 21 (Temurin)'=[bool](Find-Jdk21);'Android Studio'=[bool](Find-AndroidStudio)}
    foreach($item in $script:WingetPackages.GetEnumerator()){
        if(!$present[$item.Key]){Install-WingetPackage $item.Key $item.Value}
        else{Say "[OK] $($item.Key) ja esta instalado. Preservado." 'Green'}
    }
    Refresh-Path
    $jdk=Find-Jdk21
    if(!$jdk){throw 'JDK 21 nao identificado apos winget. Confira a instalacao; nao usarei Java de versao errada.'}
    $env:JAVA_HOME=$jdk
    $env:Path=(Join-Path $jdk 'bin')+';'+$env:Path
    $git=Find-Git
    if($git){$env:Path=(Split-Path $git -Parent)+';'+$env:Path}
    $sdk=Find-Sdk
    if(!$sdk){throw 'LOCALAPPDATA/Android SDK nao disponivel.'}
    [IO.Directory]::CreateDirectory($sdk) | Out-Null
    $env:ANDROID_HOME=$sdk; $env:ANDROID_SDK_ROOT=$sdk
    $manager=Find-SdkManager $sdk
    if(!$manager){
        Say 'SDK cmdline-tools ainda nao instalado; obtendo indice oficial do Google...' 'Yellow'
        Install-CmdlineTools $sdk
        $manager=Find-SdkManager $sdk
    }
    if(!$manager){throw 'Nao foi possivel localizar sdkmanager. Use Android Studio > SDK Manager > SDK Tools > Android SDK Command-line Tools.'}
    Say 'Verificando licencas Android ANTES de instalar os pacotes. Leia e aceite os termos do Google, se concordar.' 'Yellow'
    & $manager ('--sdk_root='+$sdk) --licenses
    if($LASTEXITCODE -ne 0){throw 'Licencas Android nao aceitas. A instalacao dos pacotes nao sera iniciada.'}
    Say 'Instalando pacotes Android necessarios; o SDK Manager pode baixar varios gigabytes.' 'Yellow'
    # Android 17 platform is published as platforms;android-37.0, not android-37.
    # Channel 3 exposes exact preview package IDs when stable repositories do not list them.
    & $manager ('--sdk_root='+$sdk) @($script:RequiredSDK) '--channel=3'
    if($LASTEXITCODE -ne 0){throw "SDK Manager falhou (codigo $LASTEXITCODE). Verifique licencas, espaco em disco, rede e versoes solicitadas."}
    # sdkmanager can warn about a missing package and still return success; verify every pinned package on disk.
    $missingSdkPackages=@($script:RequiredSDK | Where-Object { -not (Check-SdkPackage $sdk $_) })
    if($missingSdkPackages.Count -gt 0){
        throw ("SDK incompleto apos a instalacao. Pacotes ausentes: " + ($missingSdkPackages -join ', ') + ". O build nao sera iniciado.")
    }
    Say '[OK] Todos os pacotes SDK fixados foram encontrados no disco com source.properties.' 'Green'
    Say 'Dependencias conferidas. Execute a opcao 1 para revisar o relatorio.' 'Green'
}
function Install-CmdlineTools([string]$Sdk){
    # Google publishes this Windows package AND its SHA-256 on https://developer.android.com/studio
    # Pin both together: do not derive a 256-bit checksum from the repository XML (which can publish SHA-1).
    # Verified on 2026-10-21. Update the pair only after consulting Google's official download page.
    $archiveName='commandlinetools-win-15859902_latest.zip'
    $expectedSHA256='90ae805d20434428bffcb699c290860f19bb5f66a67e6b330067e3de801fb04a'
    $download='https://dl.google.com/android/repository/'+$archiveName
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
    $work=Join-Path $script:Workspace 'downloads'
    [IO.Directory]::CreateDirectory($work) | Out-Null
    $zip=Join-Path $work $archiveName
    if(Test-Path -LiteralPath $zip -PathType Leaf){
        Say 'Arquivo Command-line Tools ja baixado; validando o cache pelo SHA-256 oficial.' 'Cyan'
    }else{
        Say "Baixando Command-line Tools 22.0 oficiais do Google: $archiveName" 'Yellow'
        Invoke-WebRequest -UseBasicParsing -Uri $download -OutFile ($zip+'.partial') -TimeoutSec 900
        $downloadHash=(Get-FileHash -LiteralPath ($zip+'.partial') -Algorithm SHA256).Hash
        if($downloadHash -ine $expectedSHA256){
            throw "SHA-256 do download nao confere com o hash publicado pelo Google. Instalacao interrompida. Esperado: $expectedSHA256; obtido: $downloadHash"
        }
        Move-Item -LiteralPath ($zip+'.partial') -Destination $zip
    }
    $actual=(Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash
    if($actual -ine $expectedSHA256){
        throw "Arquivo SDK em cache tem SHA-256 diferente do publicado pelo Google. Nao sera extraido: $zip"
    }
    Say "[OK] SHA-256 oficial confirmado: $actual" 'Green'
    $temp=Join-Path $work ('cmdtools-'+[Guid]::NewGuid().ToString('N'))
    Expand-Archive -LiteralPath $zip -DestinationPath $temp
    $source=Join-Path $temp 'cmdline-tools'
    if(!(Test-Path -LiteralPath (Join-Path $source 'bin\sdkmanager.bat') -PathType Leaf)){
        throw 'ZIP oficial extraido sem sdkmanager.bat; instalacao interrompida.'
    }
    if(!(Test-Path -LiteralPath (Join-Path $source 'source.properties') -PathType Leaf)){
        throw 'ZIP oficial extraido sem source.properties; instalacao interrompida.'
    }
    $dest=Join-Path $Sdk 'cmdline-tools\latest'
    if(Test-Path -LiteralPath $dest){
        throw 'SDK cmdline-tools/latest ja existe, mas nao e utilizavel; recusado sobrescrever. Revise a pasta manualmente.'
    }
    [IO.Directory]::CreateDirectory((Split-Path $dest -Parent)) | Out-Null
    Move-Item -LiteralPath $source -Destination $dest
    Say '[OK] Command-line Tools Google 22.0 instaladas e verificadas com SHA-256.' 'Green'
}
function Set-LocalProcessEnvironment {
    # Prevent new __pycache__ entries in user checkouts during the Python host gates.
    $env:PYTHONDONTWRITEBYTECODE='1'
    Refresh-Path
    $jdk=Find-Jdk21
    if(!$jdk){throw 'JDK21 ausente; execute a opcao 2.'}
    $env:JAVA_HOME=$jdk
    $env:Path=(Join-Path $jdk 'bin')+';'+$env:Path
    $git=Find-Git
    if($git){$env:Path=(Split-Path $git -Parent)+';'+$env:Path}
    $sdk=Find-Sdk
    if(!$sdk -or !(Test-Path -LiteralPath $sdk)){throw 'SDK Android ausente; execute a opcao 2.'}
    $env:ANDROID_HOME=$sdk
    $env:ANDROID_SDK_ROOT=$sdk
    $env:Path=(Join-Path $sdk 'platform-tools')+';'+$env:Path
}
function Ensure-PolarisCheckout {
    $git=Find-Git
    if(!$git){throw 'Git ausente. Execute a instalacao primeiro.'}
    $primary=Join-Path $script:Workspace 'Polaris'
    # The primary checkout belongs to the user; never discard any changes in it.
    # A dirty checkout may contain generated Python cache files from earlier test runs.
    if(!(Test-Path -LiteralPath $script:PolarisDir)){
        if($script:PolarisDir -ne $primary){throw 'Copia isolada ausente; interrompido sem tocar no checkout original.'}
        [IO.Directory]::CreateDirectory($script:Workspace) | Out-Null
        Say ('Baixando Polaris na branch '+$script:Branch+'...') 'Yellow'
        & $git clone --branch $script:Branch --single-branch $script:Repo $script:PolarisDir
        if($LASTEXITCODE -ne 0){throw 'Git clone do Polaris falhou. Nada sera sobrescrito.'}
    }
    if(!(Test-Path -LiteralPath (Join-Path $script:PolarisDir '.git'))){throw 'Pasta Polaris existente nao e checkout Git; nao sobrescrever.'}
    $branch=(& $git -C $script:PolarisDir branch --show-current 2>$null | Out-String).Trim()
    if($LASTEXITCODE -ne 0 -or $branch -ne $script:Branch){
        throw "Polaris branch divergente ($branch); nao farei reset/checkout automatico."
    }
    $origin=(& $git -C $script:PolarisDir remote get-url origin 2>$null | Out-String).Trim()
    if($LASTEXITCODE -ne 0 -or $origin -notmatch '(?i)(github\.com[:/])Hailton-Reis/Polaris(\.git)?$'){
        throw "Repositorio origin inesperado ($origin). Nao executarei scripts deste checkout."
    }
    $dirty=(& $git -C $script:PolarisDir status --porcelain --untracked-files=normal | Out-String).Trim()
    if($LASTEXITCODE -ne 0){throw 'Nao foi possivel verificar o estado local do Polaris.'}
    if($dirty){
        Say ('[ATENCAO] Checkout possui alteracoes locais: '+$script:PolarisDir) 'Yellow'
        Say $dirty 'Yellow'
        if($script:PolarisDir -ne $primary){
            throw 'Copia isolada Polaris foi modificada. Nao sobrescrever; verifique o log.'
        }
        # Never auto-stash, reset, clean, move or delete the user's files.
        # Clone trusted remote into a fresh path instead; preserve primary checkout as-is.
        $copies=Join-Path $script:Workspace 'PolarisBuildCopies'
        [IO.Directory]::CreateDirectory($copies) | Out-Null
        $newName='checkout-'+(Get-Date).ToString('yyyyMMdd-HHmmss')+'-'+[Guid]::NewGuid().ToString('N').Substring(0,8)
        $isolated=Join-Path $copies $newName
        if(Test-Path -LiteralPath $isolated){throw 'Caminho isolado ja existe. Nenhum arquivo sobrescrito.'}
        Say '[AVISO] Copia original preservada. Criando clone LIMPO separado para este build.' 'Yellow'
        Say ('Clone de build: '+$isolated) 'Cyan'
        & $git clone --branch $script:Branch --single-branch $script:Repo $isolated
        if($LASTEXITCODE -ne 0){throw 'Clone limpo do Polaris falhou. Copia original preservada.'}
        $script:PolarisDir=$isolated
        $cloneHead=(& $git -C $isolated rev-parse HEAD | Out-String).Trim()
        if($LASTEXITCODE -ne 0 -or $cloneHead -notmatch '^[0-9a-f]{40}$'){throw 'Clone isolado sem commit verificavel.'}
        $cloneOrigin=(& $git -C $isolated remote get-url origin | Out-String).Trim()
        if($LASTEXITCODE -ne 0 -or $cloneOrigin -notmatch '(?i)(github\.com[:/])Hailton-Reis/Polaris(\.git)?$'){
            throw 'Clone isolado com origin inesperado; interrompido.'
        }
        $cloneBranch=(& $git -C $isolated branch --show-current | Out-String).Trim()
        if($LASTEXITCODE -ne 0 -or $cloneBranch -ne $script:Branch){throw 'Clone isolado com branch inesperada.'}
        $cloneDirty=(& $git -C $isolated status --porcelain --untracked-files=normal | Out-String).Trim()
        if($LASTEXITCODE -ne 0 -or $cloneDirty){throw 'Clone isolado nao esta limpo; build bloqueado.'}
        Say ('[OK] Clone isolado verificado no commit '+$cloneHead) 'Green'
        return
    }
    Say 'Conferindo a versao atual da branch Polaris...' 'Cyan'
    & $git -C $script:PolarisDir fetch --no-tags origin $script:Branch
    if($LASTEXITCODE -ne 0){throw 'Git fetch falhou; checkout existente foi preservado.'}
    $localHead=(& $git -C $script:PolarisDir rev-parse HEAD | Out-String).Trim()
    if($LASTEXITCODE -ne 0){throw 'Falha na leitura do commit local do Polaris.'}
    $remoteHead=(& $git -C $script:PolarisDir rev-parse FETCH_HEAD | Out-String).Trim()
    if($LASTEXITCODE -ne 0){throw 'Falha na leitura do commit remoto do Polaris.'}
    if($localHead -ne $remoteHead){
        & $git -C $script:PolarisDir merge-base --is-ancestor $localHead $remoteHead
        if($LASTEXITCODE -ne 0){throw 'Commits locais divergem da branch do GitHub; recusado reset ou rebase.'}
        & $git -C $script:PolarisDir merge --ff-only FETCH_HEAD
        if($LASTEXITCODE -ne 0){throw 'Fast-forward falhou; nenhum reset ou rebase realizado.'}
        Say ('[OK] Polaris atualizado: '+$remoteHead) 'Green'
    } else {
        Say ('[OK] Polaris ja atualizado: '+$localHead) 'Green'
    }
    $postDirty=(& $git -C $script:PolarisDir status --porcelain --untracked-files=normal | Out-String).Trim()
    if($LASTEXITCODE -ne 0 -or $postDirty){throw 'Checkout ficou alterado apos sincronizacao. Build bloqueado.'}
    Say '[OK] Polaris pronto na branch e origin corretos.' 'Green'
}
function Ensure-GitBashPythonShim {
    # Git Bash needs `python3`, but Windows often only supplies `py -3`/`python.exe`.
    # This shim is private to PolarisDev and never changes a system Python installation.
    $py=Find-Python
    if(!$py -or !$py.exe){throw 'Python 3.10+ nao localizado para Git Bash.'}
    $dir=Join-Path $script:Workspace 'tools\bin'
    [IO.Directory]::CreateDirectory($dir) | Out-Null
    $shim=Join-Path $dir 'python3'
    $body='#!/usr/bin/env bash' + "`n" + 'exec "$(cygpath -u "$POLARIS_WINDOWS_PYTHON")" "$@"' + "`n"
    [IO.File]::WriteAllText($shim,$body,(New-Object System.Text.UTF8Encoding($false)))
    $env:POLARIS_WINDOWS_PYTHON=$py.exe
    $env:Path=$dir+';'+$env:Path
}
function Invoke-PythonRunner([string]$Mode){
    $py=Find-Python
    if(!$py){throw 'Python 3.10+ nao encontrado. Execute a opcao de instalacao primeiro.'}
    $script=Join-Path $script:PolarisDir 'tools\local-android\polaris_local.py'
    if(!(Test-Path -LiteralPath $script -PathType Leaf)){throw 'Ferramenta Polaris local ausente; checkout incompleto.'}
    $pythonArgs=@($py.args) + @($script,$Mode,'--workspace',$script:BuildWorkspace)
    $pythonExecutable=[string]$py.run
    Say "Rodando orquestrador existente: $Mode" 'Cyan'
    & $pythonExecutable @pythonArgs
    if($LASTEXITCODE -ne 0){throw "Polaris local '${Mode}' encerrou com codigo $LASTEXITCODE. Confira logs e o diagnostico."}
}
function Prepare-Polaris {
    Set-LocalProcessEnvironment
    Ensure-PolarisCheckout
    Invoke-PythonRunner 'prepare'
    Say '[OK] Ambiente de fontes preparado. Sem alterar outros projetos.' 'Green'
}
function Build-Polaris {
    Set-LocalProcessEnvironment
    Ensure-PolarisCheckout
    # O orquestrador existing check detecta SDKs faltantes antes de iniciar o build.
    $git=Find-Git
    $src=Join-Path $script:BuildWorkspace 'Yomotsu-pinned'
    if(!(Test-Path -LiteralPath (Join-Path $src '.git'))){Invoke-PythonRunner 'prepare'}
    Ensure-GitBashPythonShim
    Invoke-PythonRunner 'build'
    Say ('[OK] Verifique os APKs e logs em '+(Join-Path $script:BuildWorkspace 'evidence')) 'Green'
    Say 'Lembrete: B01-B05 precisam de celular/emulador; o backup v2 permanece bloqueado.' 'Yellow'
}
function Invoke-PolarisEmulator([string]$Stage){
    if($Stage -notin @('baseline','spike001','duo')){throw 'Etapa do emulador nao reconhecida.'}
    Say '=== EMULADOR POLARIS ANDROID STUDIO API 35 ===' 'Cyan'
    Say 'AVDs separados: Yomotsu original e Polaris Spike-001, com dados persistentes; nenhum celular fisico.' 'Yellow'
    Say 'A instalacao da imagem Android pode ocupar varios GB; Windows WHPX e necessario.' 'Yellow'
    if($Stage -eq 'baseline'){
        if(!(Confirm-Action 'Preparar AVD Yomotsu separado, instalar e abrir baseline (A01)?')){throw 'Teste A01 cancelado.'}
    }elseif($Stage -eq 'spike001'){
        Say 'Polaris Spike-001 usa seu proprio AVD; nao substitui a baseline e preserva seus dados de teste.' 'Yellow'
        if(!(Confirm-Action 'Iniciar emulador Polaris Spike-001 independente (A02)?')){throw 'Teste A02 cancelado.'}
    }else{
        Say 'Abrir dois emuladores simultaneos pode exigir 16 GB de RAM ou mais.' 'Yellow'
        Say 'Cada Android tera fontes, biblioteca e preferencias independentes e persistentes.' 'Cyan'
        if(!(Confirm-Action 'Abrir os DOIS AVDs lado a lado, instalar os APKs validados e preservar as configuracoes?')){throw 'Teste comparativo cancelado.'}
    }
    Set-LocalProcessEnvironment
    Ensure-PolarisCheckout
    $py=Find-Python
    if(!$py){throw 'Python ausente para executar o emulador.'}
    $runner=Join-Path $script:PolarisDir 'tools\local-android\polaris_emulator.py'
    if(!(Test-Path -LiteralPath $runner -PathType Leaf)){throw 'Driver de emulador ausente no checkout Polaris.'}
    $pythonExe=[string]$py.run
    $pythonArgs=@($py.args) + @($runner,$Stage,'--workspace',$script:Workspace,'--consent')
    & $pythonExe @pythonArgs
    if($LASTEXITCODE -ne 0){throw "Teste no emulador encerrou com codigo $LASTEXITCODE. Revise PolarisDev\relatorios e PolarisDev\emulador."}
    Say ('[OK] Teste '+$Stage+' iniciado. Polaris abre em Full HD automaticamente. Confirme a tela no Android Studio; sem PASS automatico de runtime.') 'Green'
}

function Invoke-PolarisSmoke {
    Say '=== POLARIS: TESTE AUTOMATICO SEM CONFIGURAR FONTES ===' 'Cyan'
    Say 'Ambos os emuladores devem estar abertos. Nao sera feito clique, instalacao, login ou Wipe Data.' 'Yellow'
    Say 'Capturas de tela e relatorios ficarao SOMENTE no computador, em PolarisDev\\relatorios.' 'Yellow'
    if(!(Confirm-Action 'Verificar os dois AVDs sem alterar seus dados e salvar capturas locais das telas?')){
        throw 'Teste automatico cancelado. Nenhum AVD alterado.'
    }
    Set-LocalProcessEnvironment
    Ensure-PolarisCheckout
    $py=Find-Python
    if(!$py){throw 'Python indisponivel para executar o teste automatico.'}
    $runner=Join-Path $script:PolarisDir 'tools\local-android\polaris_smoke.py'
    if(!(Test-Path -LiteralPath $runner -PathType Leaf)){
        throw 'Verificador Polaris de emuladores nao localizado apos sincronizacao Git.'
    }
    $pythonExe=[string]$py.run
    $args=@($py.args) + @($runner,'--workspace',$script:Workspace,'--consent')
    & $pythonExe @args
    if($LASTEXITCODE -ne 0){throw "Teste automatico encontrou problemas (codigo $LASTEXITCODE). Consulte PolarisDev\relatorios\smoke-A01-A02-*."}
    Say '[OK] Diagnosticos A01/A02 coletados. B01-B05 continuam aguardando fontes configuradas.' 'Green'
}

function Invoke-TranslationDiagnostic([string]$Mode){
    Set-LocalProcessEnvironment
    Ensure-PolarisCheckout
    $py=Find-Python
    if(!$py){throw 'Python indisponivel para o diagnostico de traducao.'}
    $runner=Join-Path $script:PolarisDir 'tools\local-android\polaris_translation_capture.py'
    if(!(Test-Path -LiteralPath $runner -PathType Leaf)){throw 'Atualize o checkout Polaris para obter o coletor de traducao.'}
    if($Mode -eq 'capture'){
        Say 'Abra o capitulo no emulador Polaris em faixa longa e traduza antes de continuar.' 'Yellow'
        Say 'A coleta comeca na posicao atual. Nao toque no leitor durante as capturas.' 'Yellow'
        Say 'Arquivos ficam no PC; nenhuma traducao ou envio de arquivos sera iniciado.' 'Cyan'
    }
    $pythonExe=[string]$py.run
    $pythonArgs=@($py.args) + @($runner,$Mode,'--workspace',$script:Workspace,'--consent')
    if($Mode -eq 'capture'){$pythonArgs+=@('--interactive')}
    & $pythonExe @pythonArgs
    if($LASTEXITCODE -ne 0){throw 'Diagnostico interrompido. Confira a mensagem e os relatorios locais.'}
}

function Other-Projects {
    Say '=== FERRAMENTAS RELACIONADAS A OUTROS PROJETOS (somente leitura) ===' 'Cyan'
    foreach($p in @(@('Analista/Madeira','python.exe'),@('CameraGuard','.NET'),@('Vai Quem Quer','node.exe'))){
       $program=if($p[1] -eq '.NET'){'dotnet.exe'}else{$p[1]}
       $exe=CmdPath $program
       if($exe){ Say ('[OK] '+$p[0]+': '+$exe) 'Green' }else{ Say ('[OPCIONAL] '+$p[0]+': '+$program+' nao encontrado') 'Yellow' }
    }
    Say 'Nenhum arquivo, gravacao, banco de dados, release ou dependencia desses projetos foi modificado.'
}
function Install-OtherTools {
    Say '=== FERRAMENTAS OPCIONAIS DOS OUTROS PROJETOS ===' 'Cyan'
    Say 'Node LTS ajuda projetos web; SDK .NET 8 generico NAO substitui o .NET 8.0.425 fixado do CameraGuard.' 'Yellow'
    Say 'Nao executaremos npm install, scripts de CameraGuard ou fontes existentes.'
    if(!(Confirm-Action 'Instalar Node.js LTS e SDK .NET 8 ausentes, sem tocar nos projetos?')){throw 'Instalacao opcional cancelada.'}
    if(!(CmdPath 'node.exe')){Install-WingetPackage 'Node.js LTS' 'OpenJS.NodeJS.LTS'}else{Say '[OK] Node.js ja presente; preservado.' 'Green'}
    if(!(CmdPath 'dotnet.exe')){Install-WingetPackage 'SDK .NET 8' 'Microsoft.DotNet.SDK.8'}else{Say '[OK] dotnet presente; preservado.' 'Green'}
    Say 'Ferramentas opcionais concluidas. Confirme versoes especificas nos proprios projetos.' 'Green'
}
function Run-Action([string]$Chosen){
    switch($Chosen){
        '1' { [void](Get-Status) }
        '2' { Install-Tools }
        '3' { Prepare-Polaris }
        '4' { Build-Polaris }
        '5' { [void](Get-Status); Other-Projects }
        '6' { [void](Get-Status); Install-Tools; [void](Get-Status); Prepare-Polaris; Build-Polaris }
        '7' { Install-OtherTools }
        '8' { Invoke-PolarisEmulator 'baseline' }
        '9' { Invoke-PolarisEmulator 'spike001' }
        '10' { Invoke-PolarisEmulator 'duo' }
        '11' { Invoke-PolarisSmoke }
        '12' { Invoke-TranslationDiagnostic 'capture' }
        '13' { Invoke-TranslationDiagnostic 'display' }
        '14' { Invoke-TranslationDiagnostic 'restore' }
        '0' { Say 'Saindo sem alterar arquivos.';return }
        default { Say '[ERRO] Opcao invalida.' 'Yellow' }
    }
}
function Menu {
    do {
        Write-Host ''
        Write-Host '===== POLARIS - CMD UNICO - REVISAO DE TRADUCAO 02/11 =====' -ForegroundColor Cyan
        Write-Host '1. Verificar TUDO (somente diagnostico; salva log em PolarisDev)'
        Write-Host '2. Instalar/configurar ferramentas ausentes (winget + SDK)'
        Write-Host '3. Preparar Polaris + Yomotsu (Git)'
        Write-Host '4. Compilar APK localmente (sem GitHub Actions)'
        Write-Host '5. Verificar ferramentas dos outros projetos'
        Write-Host '6. FAZER TUDO DO POLARIS: instalar + preparar + compilar'
        Write-Host '7. Instalar Node.js/.NET 8 OPCIONAIS (outros projetos)'
        Write-Host '8. EMULAR Yomotsu original (Android Studio / A01)'
        Write-Host '9. EMULAR Polaris (AVD separado / Full HD automatico)'
        Write-Host '10. COMPARAR lado a lado: Yomotsu + Polaris (2 AVDs, dados salvos)'
        Write-Host '11. TESTES AUTOMATICOS sem repositorios (sem modificar os 2 AVDs)'
        Write-Host '12. COMPARAR traducao: capturas + original + registro do capitulo aberto'
        Write-Host '13. REAPLICAR tela FHD manualmente (opcional; 9 e 10 ja ajustam)'
        Write-Host '14. RESTAURAR os ajustes manuais anteriores da tela'
        Write-Host '0. Sair'
        $choice=Read-Host 'Escolha'
        if($choice -eq '0'){break}
        try{Run-Action $choice}catch{
            $script:HadMenuFailure=$true
            Say ('[ERRO] '+$_.Exception.Message) 'Red'
            Say 'Uma falha ocorreu nesta sessao; o CMD principal retornara codigo diferente de zero ao sair.' 'Yellow'
        }
    }while($true)
    if($script:HadMenuFailure){throw 'Uma ou mais operacoes falharam. Consulte o log antes de considerar a configuracao concluida.'}
}
New-Session
try{
    switch($Action){
        Menu { Menu }
        Check { [void](Get-Status) }
        Install { Install-Tools }
        Prepare { Prepare-Polaris }
        Build { Build-Polaris }
        All { [void](Get-Status);Install-Tools;[void](Get-Status);Prepare-Polaris;Build-Polaris }
        OtherProjects { Other-Projects }
        EmulatorBaseline { Invoke-PolarisEmulator 'baseline' }
        EmulatorPatched { Invoke-PolarisEmulator 'spike001' }
        EmulatorDuo { Invoke-PolarisEmulator 'duo' }
        EmulatorSmoke { Invoke-PolarisSmoke }
        TranslationCapture { Invoke-TranslationDiagnostic 'capture' }
        EmulatorDisplay { Invoke-TranslationDiagnostic 'display' }
        EmulatorDisplayRestore { Invoke-TranslationDiagnostic 'restore' }
    }
    Say ('Logs: '+$script:LogFile) 'Cyan'
    exit 0
}catch{
    Say ('[FALHOU] '+$_.Exception.Message) 'Red'
    Say ('Log: '+$script:LogFile)
    exit 2
}finally{
    if($script:TranscriptStarted){
        try{Stop-Transcript | Out-Null}catch{}
    }
}