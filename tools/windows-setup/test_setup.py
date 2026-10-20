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
    def test_cmd_uses_local_ps_file_and_not_untrusted_eval(self):
        self.assertIn('powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Polaris_Setup.ps1"',CMD)
        self.assertNotIn('-NonInteractive',CMD)
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
        self.assertIn('https://dl.google.com/android/repository/repository2-1.xml',PS)
        self.assertIn('Get-FileHash',PS)
        self.assertIn("-Algorithm SHA256",PS)
        self.assertIn('O indice oficial nao inclui SHA-256 verificavel',PS)
        self.assertIn('sha256',PS)
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