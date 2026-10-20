#!/usr/bin/env python3
"""Polaris R001: build the pinned Android baseline/Spike-001 WITHOUT GitHub Actions.

Host-only orchestration. Does not patch user databases, install APKs, alter
Android devices, or modify the Polaris repository. Requires user-run commands.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime

PINNED = "0fb80c439ef816eeb50674f1b90af39918b176d8"
BRANCH = "r001/multisource-foundation"
YOMOTSU_URL = "https://github.com/kiritsuguxs/yomotsu.git"
SDK_REQUIREMENTS = (
    "platforms/android-37",
    "build-tools/36.0.0",
    "build-tools/37.0.0",
    "ndk/29.0.14206865",
    "ndk/28.2.13676358",
    "cmake/3.22.1",
)


def polaris_root() -> Path:
    return Path(__file__).resolve().parents[2]


def git_bash_path() -> Path | None:
    if os.name != "nt":
        binary = shutil.which("bash")
        return Path(binary) if binary else None
    locations: list[Path] = []
    git = shutil.which("git")
    if git:
        git_path = Path(git).resolve()
        locations += [git_path.parent.parent / "bin/bash.exe", git_path.parent / "bash.exe"]
    for env_name in ("ProgramFiles", "ProgramFiles(x86)"):
        home = os.getenv(env_name)
        if home:
            locations.append(Path(home) / "Git/bin/bash.exe")
    for candidate in locations:
        if candidate.is_file():
            return candidate
    return None  # Don't accidentally execute Windows WSL bash.exe.


def android_sdk() -> Path | None:
    for key in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        p = os.getenv(key)
        if p and Path(p).is_dir():
            return Path(p).resolve()
    if os.name == "nt":
        base = os.getenv("LOCALAPPDATA")
        if base:
            p = Path(base) / "Android/Sdk"
            if p.is_dir():
                return p.resolve()
    return None


def java_is_21(output: str) -> bool:
    return bool(re.search(r'\bversion\s+"21(?:\.|\")|\bopenjdk\s+21(?:\.|\s)', output))


def bash_prelude() -> str:
    # No interpolation of paths into shell code. Environment vars carry paths.
    if os.name == "nt":
        return ('set -euo pipefail; '
                'command -v cygpath >/dev/null || { echo "Git Bash cygpath ausente" >&2; exit 15; }; '
                'if [ -n "${JAVA_HOME:-}" ]; then export JAVA_HOME="$(cygpath -u "$JAVA_HOME")"; fi; '
                'exec bash "$(cygpath -u "$POLARIS_REPO")/scripts/r001/build_issue002.sh" '
                '"$(cygpath -u "$POLARIS_YOMOTSU")" "$(cygpath -u "$POLARIS_EVIDENCE")"')
    return ('set -euo pipefail; '
            'exec bash "$POLARIS_REPO/scripts/r001/build_issue002.sh" '
            '"$POLARIS_YOMOTSU" "$POLARIS_EVIDENCE"')


def run_capture(command: list[str]) -> tuple[int, str]:
    try:
        p = subprocess.run(command, text=True, capture_output=True, timeout=25, check=False)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, str(exc)


def preflight(root: Path, strict: bool) -> bool:
    print("Polaris R001 | diagnóstico local (sem GitHub Actions)")
    print(f"Polaris: {root}")
    ok = True
    if not (root / "spikes/spike001/apply_spike001.py").exists():
        print("[FALTA] Checkout COMPLETO do repositório Polaris.")
        ok = False
    git = shutil.which("git")
    if git:
        code, branch = run_capture([git, "-C", str(root), "branch", "--show-current"])
        if code == 0:
            print(f"[OK] Git; branch: {branch.strip() or '(detached)'}")
            if branch.strip() != BRANCH:
                print(f"[AVISO] Use a branch {BRANCH}; nenhuma alteração automática será feita.")
                if strict:
                    ok = False
        else:
            print("[AVISO] A pasta não parece ser um checkout Git válido.")
            ok = False
    else:
        print("[FALTA] Git for Windows / git")
        ok = False
    bash = git_bash_path()
    if bash:
        print(f"[OK] Bash disponível: {bash}")
        code, info = run_capture([str(bash), "-c", 'for command_name in realpath base64 tee python3; do command -v "$command_name" >/dev/null || exit 1; done'])
        if code:
            print("[FALTA] Bash precisa ter realpath, base64, tee e python3 no PATH.")
            print("        Instale Git for Windows e Python 3; confirme python3 no Git Bash.")
            if strict:
                ok = False
    else:
        print("[FALTA] Git Bash (Windows) ou Bash (Linux/macOS).")
        ok = False
    python = sys.version_info
    if python.major == 3 and python.minor >= 10:
        print(f"[OK] Python {python.major}.{python.minor}.{python.micro}")
    else:
        print("[FALTA] Python 3.10 ou posterior")
        ok = False
    java = shutil.which("java")
    if java:
        code, output = run_capture([java, "-version"])
        if code == 0 and java_is_21(output):
            print("[OK] JDK/Java 21 encontrado")
        else:
            print("[FALTA] JDK 21 em JAVA_HOME/PATH. Java detectado:")
            print("       " + output.splitlines()[0][:180] if output else "       versão indisponível")
            if strict:
                ok = False
    else:
        print("[FALTA] JDK 21 (Temurin 21 ou Android Studio JDK 21)")
        if strict:
            ok = False
    java_home = os.getenv("JAVA_HOME")
    if java_home:
        candidate = Path(java_home) / "bin" / ("java.exe" if os.name == "nt" else "java")
        if not candidate.is_file():
            print("[FALTA] JAVA_HOME não aponta para um JDK válido.")
            if strict:
                ok = False
        else:
            rc, home_output = run_capture([str(candidate), "-version"])
            if rc != 0 or not java_is_21(home_output):
                print("[FALTA] JAVA_HOME precisa apontar para JDK 21; Gradle pode ignorar o Java do PATH.")
                if strict:
                    ok = False
    sdk = android_sdk()
    if sdk:
        print(f"[OK] Android SDK: {sdk}")
        missing = [p for p in SDK_REQUIREMENTS if not (sdk / p).is_dir()]
        if missing:
            print("[FALTA] Instale no Android Studio > SDK Manager > Show Package Details:")
            for item in missing:
                print("      " + item)
            if strict:
                ok = False
        else:
            print("[OK] Plataforma 37, Build Tools, NDKs e CMake")
    else:
        print("[FALTA] Android SDK. Instale Android Studio e SDK Platform 37.")
        if strict:
            ok = False
    return ok


def git_call(args: list[str], *, cwd: Path | None = None) -> None:
    print("Git:", " ".join(args))
    result = subprocess.run(["git", *args], cwd=cwd, check=False)
    if result.returncode != 0:
        raise RuntimeError("Falha do Git; checkout não foi alterado à força.")


def ensure_yomotsu(workspace: Path) -> Path:
    target = workspace / "Yomotsu-pinned"
    if not target.exists():
        workspace.mkdir(parents=True, exist_ok=True)
        git_call(["clone", YOMOTSU_URL, str(target)])
        git_call(["checkout", "--detach", PINNED], cwd=target)
    if not (target / ".git").exists():
        raise RuntimeError(f"{target} já existe, mas não é repositório Git: interrompido.")
    code, head = run_capture(["git", "-C", str(target), "rev-parse", "HEAD"])
    if code != 0 or head.strip() != PINNED:
        raise RuntimeError("Yomotsu precisa estar no commit fixado; não alterarei checkout existente.")
    code, changes = run_capture(["git", "-C", str(target), "status", "--porcelain"])
    if code != 0 or changes.strip():
        raise RuntimeError("Checkout Yomotsu não está limpo. Use outra pasta/clone; não sobrescreverei alterações.")
    print("[OK] Yomotsu fixado e limpo:", PINNED)
    return target


def choose_evidence_dir(workspace: Path, custom: Path | None) -> Path:
    folder = custom or (workspace / "evidence" / datetime.now().strftime("issue002-%Y%m%d-%H%M%S"))
    if folder.exists():
        raise RuntimeError(f"Evidência já existe: {folder}. Não sobrescreverei relatórios ou APKs.")
    return folder.resolve()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("check", "prepare", "build"), help="check = sem mudanças; prepare = baixar Yomotsu; build = compilar")
    p.add_argument("--workspace", type=Path, default=Path.home() / "PolarisLocal", help="pasta para Yomotsu e evidências")
    p.add_argument("--evidence-dir", type=Path, help="caminho novo de evidências (somente build)")
    args = p.parse_args(argv)
    root = polaris_root()
    if args.action == "check":
        ready = preflight(root, strict=True)
        print("[PRONTO] Ambiente apto a tentar build." if ready else "[PENDENTE] Corrija os itens [FALTA] acima.")
        return 0 if ready else 2
    if not shutil.which("git"):
        print("Git é obrigatório antes de clonar/build.", file=sys.stderr)
        return 2
    if not (root / "scripts/r001/build_issue002.sh").exists():
        print("Use um checkout completo do Polaris, não só um ZIP de testes.", file=sys.stderr)
        return 2
    try:
        if args.action == "prepare":
            ensure_yomotsu(args.workspace.expanduser().resolve())
            return 0
        if not preflight(root, strict=True):
            return 2
        workspace = args.workspace.expanduser().resolve()
        source = ensure_yomotsu(workspace)
        evidence = choose_evidence_dir(workspace, args.evidence_dir.expanduser() if args.evidence_dir else None)
        sdk = android_sdk()
        bash = git_bash_path()
        assert sdk and bash
        env = os.environ.copy()
        env["ANDROID_HOME"] = str(sdk)
        env["ANDROID_SDK_ROOT"] = str(sdk)
        env["POLARIS_REPO"] = str(root)
        env["POLARIS_YOMOTSU"] = str(source)
        env["POLARIS_EVIDENCE"] = str(evidence)
        print("\nA execução fará baseline + Spike-001 + testes JUnit comparativos.")
        print("Evidências (não enviar sem revisar):", evidence)
        print("Não aplica migração 15, não instala APK e não consome minutos do GitHub Actions.")
        sys.stdout.flush()
        rc = subprocess.run([str(bash), "-c", bash_prelude()], env=env, check=False).returncode
        if rc != 0:
            print(f"[FALHOU] Build encerrou com código {rc}. Veja os logs em {evidence}.", file=sys.stderr)
            return rc
        print("[OK] Build finalizado. Veja APKs em:", evidence / "apks/spike001")
        print("A01/B01–B05 ainda exigem device/emulador e revisão de evidências.")
        return 0
    except (OSError, RuntimeError) as exc:
        print("[INTERROMPIDO]", exc, file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
