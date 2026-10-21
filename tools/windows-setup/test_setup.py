"""Fast static contract tests for the Windows CMD and PowerShell launcher.

These tests do NOT execute winget or simulate Android Studio, so no fake Windows PASS.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent
CMD = (ROOT / '00_POLARIS_TUDO_EM_UM.cmd').read_text(encoding='utf-8')
PS = (ROOT / 'Polaris_Setup.ps1').read_text(encoding='utf-8')
DOC = (ROOT / 'COMO_FUNCIONA.md').read_text(encoding='utf-8')

class LauncherSafety(unittest.TestCase):
    def test_cmd_is_single_file_with_embedded_powershell(self):
        self.assertIn('set "POLARIS_MAIN_CMD=%~f0"', CMD)
        self.assertIn('ReadAllText($env:POLARIS_MAIN_CMD)', CMD)
        self.assertIn('Remove-Item -LiteralPath $tmp -Force', CMD)
        self.assertIn("powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command", CMD)
        self.assertIn("powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $tmp", CMD)
        self.assertNotIn('-NonInteractive', CMD)
        marker = chr(10) + ':POLARIS_PS1_BEGIN' + chr(10)
        self.assertEqual(CMD.split(marker, 1)[1], PS)

    def test_cmd_propagates_nested_powershell_exit_status(self):
        self.assertIn('$rc=$LASTEXITCODE', CMD)
        self.assertIn('exit $rc', CMD)
        self.assertIn('set "RESULTADO=%ERRORLEVEL%"', CMD)

    def test_menu_errors_fail_closed(self):
        self.assertIn('$script:HadMenuFailure=$false', PS)
        self.assertIn('$script:HadMenuFailure=$true', PS)
        self.assertIn("if($script:HadMenuFailure){throw", PS)

    def test_full_setup_runs_diagnostics_before_and_after_install(self):
        self.assertIn("'6' { [void](Get-Status); Install-Tools; [void](Get-Status); Prepare-Polaris; Build-Polaris }", PS)
        self.assertIn("All { [void](Get-Status);Install-Tools;[void](Get-Status);Prepare-Polaris;Build-Polaris }", PS)

    def test_android_studio_registry_optional_fields_are_safe(self):
        part = PS.split('function Find-AndroidStudio {', 1)[1].split('function Find-Sdk {', 1)[0]
        self.assertIn("PSObject.Properties['DisplayName']", part)
        self.assertIn("PSObject.Properties['InstallLocation']", part)
        self.assertNotIn('$_.DisplayName', part)
        self.assertNotIn('$entry.InstallLocation', part)

    def test_jdk_detection_does_not_write_reserved_home(self):
        part = PS.split('function Find-Jdk21 {', 1)[1].split('function Find-AndroidStudio {', 1)[0]
        self.assertIn('foreach($jdkHome in', part)
        self.assertIn('return $jdkHome', part)
        self.assertNotRegex(part, r'(?im)^\s*foreach\(\$home\b')

    def test_commandline_tools_pinned_to_official_google_sha256(self):
        part = PS.split('function Install-CmdlineTools(', 1)[1].split('function Set-LocalProcessEnvironment', 1)[0]
        self.assertIn('https://developer.android.com/studio', part)
        self.assertIn('commandlinetools-win-15859902_latest.zip', part)
        self.assertIn('90ae805d20434428bffcb699c290860f19bb5f66a67e6b330067e3de801fb04a', part)
        self.assertIn('https://dl.google.com/android/repository/', part)
        self.assertIn('Get-FileHash', part)
        self.assertIn('-Algorithm SHA256', part)
        self.assertIn('if($downloadHash -ine $expectedSHA256)', part)
        self.assertIn('if($actual -ine $expectedSHA256)', part)
        self.assertNotIn('repository2-1.xml', part)
        self.assertNotIn('$host=', part)

    def test_licenses_accepted_before_sdk_package_install(self):
        installation = PS.split('function Install-Tools {', 1)[1].split('function Install-CmdlineTools(', 1)[0]
        self.assertLess(installation.index("--licenses"), installation.index("@($script:RequiredSDK)"))

    def test_no_assignments_to_reserved_powershell_variables(self):
        # This catches collisions even in new functions or future revisions.
        clean = '\n'.join(line for line in PS.splitlines() if not line.lstrip().startswith('#'))
        self.assertNotRegex(clean, r'(?im)^\s*\$(?:host|home|pid|pshome)\s*=')

    def test_cmd_handles_failures(self):
        self.assertIn('if errorlevel 1',CMD)
        self.assertIn('exit /b %RESULTADO%',CMD)
    def test_installs_exact_official_packages(self):
        for pkg in ('Google.AndroidStudio','Git.Git','Python.Python.3.13','EclipseAdoptium.Temurin.21.JDK'):
            self.assertIn(pkg,PS)
        self.assertIn('--accept-package-agreements',PS)
    def test_install_requires_confirmation(self):
        self.assertIn('Confirm-Action',PS)
        self.assertIn("-eq 'SIM'",PS)
        self.assertIn('Instalacao cancelada pelo operador.',PS)
    def test_android_sdk_and_pinned_versions(self):
        for pkg in ('android-37','36.0.0','37.0.0','29.0.14206865','28.2.13676358','3.22.1','platform-tools'):
            self.assertIn(pkg,PS)
    def test_secure_sdk_bootstrap(self):
        self.assertIn('https://dl.google.com/android/repository/',PS)
        self.assertIn('Get-FileHash',PS)
        self.assertIn("-Algorithm SHA256",PS)
        self.assertIn('if($downloadHash -ine $expectedSHA256)',PS)
        self.assertIn('if($actual -ine $expectedSHA256)',PS)
        self.assertIn('source.properties',PS)
        self.assertIn('cmdline-tools\latest',PS)
    def test_existing_checkout_protected(self):
        self.assertIn("branch divergente",PS)
        self.assertIn('Repositorio origin inesperado',PS)
        for forbidden in ('git reset --hard','git clean -fd','Remove-Item -Recurse -Force'):
            self.assertNotIn(forbidden,PS)
    def test_repo_pins_and_build_scripts(self):
        self.assertIn('r001/multisource-foundation',PS)
        self.assertIn('0fb80c439ef816eeb50674f1b90af39918b176d8',PS)
        self.assertIn('polaris_local.py',PS)
        self.assertIn("Invoke-PythonRunner 'build'",PS)
    def test_check_mode_is_separate(self):
        self.assertIn('function Get-Status {',PS)
        self.assertIn('function Install-Tools {',PS)
        part=PS.split('function Get-Status {',1)[1].split('function Confirm-Action',1)[0]
        self.assertNotIn('winget install',part)
        self.assertNotIn('Install-WingetPackage',part)
    def test_other_projects_are_read_only(self):
        p=PS.split('function Other-Projects {',1)[1].split('function Install-OtherTools',1)[0]
        self.assertNotIn('Install-WingetPackage',p)
        self.assertNotIn('Remove-Item',p)
        self.assertIn('CameraGuard',p)
        self.assertIn('Vai Quem Quer',p)
    def test_shell_shim_is_private(self):
        self.assertIn('function Ensure-GitBashPythonShim',PS)
        self.assertIn('POLARIS_WINDOWS_PYTHON',PS)
        self.assertIn("Join-Path $script:Workspace 'tools\\bin'",PS)
    def test_no_android_or_backup_mutation(self):
        self.assertNotIn('adb install ',PS)
        self.assertNotIn('migration15',PS.lower())
        self.assertIn('sem instalar APK',DOC)
    def test_menu_has_all_actions(self):
        for i in range(8):
            self.assertRegex(PS,rf"'{i}'\s*\{{|{i}\. ") if i != 6 else self.assertIn('6. FAZER TUDO DO POLARIS',PS)
    def test_other_project_install_is_optional_and_confirmed(self):
        self.assertIn("'7' { Install-OtherTools }",PS)
        part=PS.split('function Install-OtherTools {',1)[1].split('function Run-Action',1)[0]
        self.assertIn('Confirm-Action',part)
        self.assertIn('OpenJS.NodeJS.LTS',part)
        self.assertIn('Microsoft.DotNet.SDK.8',part)
    def test_no_dangerous_persistent_env_update(self):
        self.assertNotIn('SetEnvironmentVariable',PS)
        self.assertIn('function Set-LocalProcessEnvironment',PS)
    def test_documentation_discloses_no_windows_validation(self):
        self.assertIn('não** foram executados em Windows',DOC)

if __name__ == '__main__':
    unittest.main(verbosity=2)