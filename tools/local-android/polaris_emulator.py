#!/usr/bin/env python3
"""Polaris R001: isolated Android Studio AVD smoke-test driver (Windows).

Runs only after explicit operator consent from the main CMD. Never targets a
physical Android device, overwrites an existing AVD, wipes data or certifies
reader runtime acceptance merely because the launch intent was delivered.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone

AVD = "Polaris_R001_API35_x64"
IMAGE = "system-images;android-35;google_apis;x86_64"
PACKAGE = "app.mihon.tachiyomiat.dev"
APK_RE = re.compile(r"^([a-fA-F0-9]{64})\s+\*?((?:baseline|spike001)/[^/\\]+\.apk)$")


class EmulatorError(Exception):
    pass


def run(args: list[str], *, capture=True, input_text=None, timeout=120):
    try:
        return subprocess.run(args, text=True, input=input_text, capture_output=capture,
                              check=False, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise EmulatorError(f"Falha ao executar {Path(args[0]).name}: {exc}") from exc


def require_success(result, label: str):
    if result.returncode:
        detail = (result.stderr or result.stdout or "").strip()[-700:]
        raise EmulatorError(f"{label} (exit={result.returncode}): {detail}")
    return result.stdout or ""


def sdk_location() -> Path:
    for name in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        raw = os.getenv(name)
        if raw and Path(raw).is_dir():
            return Path(raw).resolve()
    raw = os.getenv("LOCALAPPDATA")
    if raw and (Path(raw) / "Android" / "Sdk").is_dir():
        return (Path(raw) / "Android" / "Sdk").resolve()
    raise EmulatorError("SDK nao localizado. Execute opcao 1 do CMD e confira Android Studio.")


def executable(sdk: Path, name: str) -> Path:
    paths = {
        "sdkmanager": sdk / "cmdline-tools" / "latest" / "bin" / "sdkmanager.bat",
        "avdmanager": sdk / "cmdline-tools" / "latest" / "bin" / "avdmanager.bat",
        "emulator": sdk / "emulator" / "emulator.exe",
        "adb": sdk / "platform-tools" / "adb.exe",
    }
    candidate = paths[name]
    if name != "emulator" and not candidate.is_file():
        raise EmulatorError(f"Ferramenta Android SDK ausente: {candidate}")
    return candidate


def check_acceleration(emulator: Path) -> None:
    report = run([str(emulator), "-accel-check"], timeout=45)
    output = (report.stdout or "") + (report.stderr or "")
    if report.returncode or not re.search(r"(installed and usable|is usable|accel:\s*0)", output, re.I):
        raise EmulatorError("Aceleracao virtual indisponivel. Ative VT-x/SVM no BIOS e "
                            "Windows Hypervisor Platform (WHPX); reinicie quando solicitado. "
                            f"Diagnostico: {output.strip()[-400:]}")


def find_device(adb: Path, avd: str = AVD) -> str | None:
    listing = run([str(adb), "devices"], timeout=20)
    require_success(listing, "adb devices")
    for line in (listing.stdout or "").splitlines():
        match = re.match(r"^(emulator-\d+)\s+device(?:\s|$)", line.strip())
        if not match:
            continue
        serial = match.group(1)
        report = run([str(adb), "-s", serial, "emu", "avd", "name"], timeout=20)
        names = (report.stdout or "").splitlines()
        if report.returncode == 0 and avd in [line.strip() for line in names]:
            return serial
    return None


def ensure_avd(workspace: Path, sdk: Path, *, boot_timeout=420) -> tuple[Path, str]:
    if os.getenv("PROCESSOR_ARCHITECTURE", "").upper() != "AMD64":
        raise EmulatorError("Este instalador so automatiza x86_64 em Windows AMD64. "
                            "Em computadores ARM64, use o Device Manager do Android Studio.")
    manager = executable(sdk, "sdkmanager")
    avdmanager = executable(sdk, "avdmanager")
    adb = executable(sdk, "adb")
    emulator = executable(sdk, "emulator")
    if not emulator.is_file():
        print("Instalando Android Emulator oficial...", flush=True)
        require_success(run([str(manager), f"--sdk_root={sdk}", "emulator"], capture=False, timeout=1800),
                        "Instalacao do Android Emulator")
    if not emulator.is_file():
        raise EmulatorError("Android Emulator nao apareceu no SDK apos instalacao.")
    check_acceleration(emulator)
    image_properties = sdk / "system-images" / "android-35" / "google_apis" / "x86_64" / "source.properties"
    if not image_properties.is_file():
        print("Baixando imagem Google Android 15/API35 x86_64 (uso exclusivo do AVD Polaris)...", flush=True)
        require_success(run([str(manager), f"--sdk_root={sdk}", IMAGE], capture=False, timeout=3600),
                        "Imagem de sistema Android 15")
    if not image_properties.is_file():
        raise EmulatorError("Imagem de sistema ainda ausente depois do SDK Manager.")
    root = workspace / "emulador"
    root.mkdir(parents=True, exist_ok=True)
    avd_path = root / "avd" / f"{AVD}.avd"
    marker = root / f"{AVD}.owner.txt"
    listing = require_success(run([str(emulator), "-list-avds"], timeout=35), "emulator -list-avds")
    present = AVD in [s.strip() for s in listing.splitlines()]
    if present and (not marker.is_file() or marker.read_text(encoding="utf-8-sig").strip() != AVD):
        raise EmulatorError("Ja existe AVD com nome Polaris, mas sem marcador de propriedade. "
                            "Para proteger dados, nao vou reutiliza-lo nem altera-lo.")
    if not present:
        if avd_path.exists() or marker.exists():
            raise EmulatorError("AVD Polaris parcialmente existente. Nada sera sobrescrito; confira Device Manager.")
        print("Criando Android Virtual Device isolado para Polaris...", flush=True)
        require_success(run([str(avdmanager), "create", "avd", "-n", AVD, "-k", IMAGE,
                             "-p", str(avd_path)], input_text="no\n", timeout=180),
                        "Criacao do AVD Polaris")
        marker.write_text(AVD + "\n", encoding="utf-8")
    serial = find_device(adb)
    if serial is None:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        out = root / f"emulator-{stamp}.stdout.log"
        err = root / f"emulator-{stamp}.stderr.log"
        print("Abrindo janela do emulador Android Studio Polaris...", flush=True)
        with out.open("wb") as stdout, err.open("wb") as stderr:
            subprocess.Popen([str(emulator), "-avd", AVD, "-no-snapshot-load", "-no-snapshot-save"],
                             stdout=stdout, stderr=stderr, creationflags=(0x00000200 if os.name == "nt" else 0))
    deadline = time.monotonic() + boot_timeout
    while time.monotonic() < deadline:
        serial = find_device(adb)
        if serial:
            completed = run([str(adb), "-s", serial, "shell", "getprop", "sys.boot_completed"], timeout=20)
            if completed.returncode == 0 and (completed.stdout or "").strip() == "1":
                api = require_success(run([str(adb), "-s", serial, "shell", "getprop",
                                           "ro.build.version.sdk"]), "Android API").strip()
                if api != "35":
                    raise EmulatorError(f"AVD inesperado: API {api} (esperada 35).")
                print(f"[OK] Emulador {AVD} online: {serial}, API {api}", flush=True)
                return adb, serial
        time.sleep(5)
    raise EmulatorError("O AVD nao inicializou. Examine PolarisDev/emulador/emulator-*.stderr.log; "
                        "verifique WHPX, virtualizacao e memoria disponivel.")


def find_apks(workspace: Path) -> tuple[dict[str, Path], Path]:
    root = workspace / "PolarisLocal" / "evidence"
    if not root.is_dir():
        raise EmulatorError("Nenhum build local encontrado. Execute opcao 4 do CMD.")
    for folder in sorted(root.glob("issue002-*"), reverse=True):
        if not (folder / "build-status.txt").is_file() or not (folder / "apks" / "SHA256SUMS.txt").is_file():
            continue
        if "APK_BUILDS_PASS_NO_NEW_UNIT_REGRESSIONS" not in (folder / "build-status.txt").read_text():
            continue
        apk_dir = folder / "apks"
        selected = {stage: list((apk_dir / stage).glob("*.apk")) for stage in ("baseline", "spike001")}
        if not all(len(v) == 1 for v in selected.values()):
            continue
        hashes = {}
        for line in (apk_dir / "SHA256SUMS.txt").read_text().splitlines():
            match = APK_RE.fullmatch(line)
            if not match:
                raise EmulatorError(f"Manifesto SHA256 invalido: {apk_dir / 'SHA256SUMS.txt'}")
            hashes[match.group(2)] = match.group(1).lower()
        result = {}
        for stage in ("baseline", "spike001"):
            apk = selected[stage][0]
            key = f"{stage}/{apk.name}"
            actual = hashlib.sha256(apk.read_bytes()).hexdigest()
            if hashes.get(key) != actual:
                raise EmulatorError(f"SHA-256 divergente para {key}. Instalacao recusada.")
            result[stage] = apk
        print(f"[OK] Build concluido e hashes APK confirmados: {apk_dir}", flush=True)
        return result, folder
    raise EmulatorError("Nao encontrei build completo com baseline, Spike-001 e hashes validos.")


def install_and_launch(adb: Path, serial: str, apk: Path, stage: str, workspace: Path, build: Path) -> Path:
    if not re.fullmatch(r"emulator-\d+", serial) or find_device(adb) != serial:
        raise EmulatorError("ADB alvo nao e nosso AVD Polaris. Nenhuma instalacao executada.")
    if stage == "spike001":
        # Only perform a debug migration test after the baseline is installed.
        listing = require_success(run([str(adb), "-s", serial, "shell", "pm", "path", PACKAGE]), "pm path")
        if "package:" not in listing:
            raise EmulatorError("Baseline ainda nao instalada neste AVD. Execute opcao 8 primeiro.")
    print(f"Instalando APK {stage} somente no emulador {serial} ...", flush=True)
    require_success(run([str(adb), "-s", serial, "install", "-r", "-t", str(apk)], timeout=240),
                    f"Instalacao APK {stage}")
    package_path = require_success(run([str(adb), "-s", serial, "shell", "pm", "path", PACKAGE]), "pm path")
    if "package:" not in package_path:
        raise EmulatorError(f"Pacote {PACKAGE} nao encontrado apos instalacao.")
    launched = require_success(run([str(adb), "-s", serial, "shell", "monkey", "-p", PACKAGE,
                                    "-c", "android.intent.category.LAUNCHER", "1"]), "Lancar aplicativo")
    if not re.search(r"Events injected:\s*1", launched):
        raise EmulatorError("Nao foi confirmada a entrega do comando de abertura do aplicativo.")
    evidence = workspace / "relatorios" / f"emulador-{stage}-{datetime.now():%Y%m%d-%H%M%S}-{os.getpid()}"
    evidence.mkdir(parents=True, exist_ok=False)
    report = {
        "project": "Polaris", "stage": stage, "avd": AVD, "serial": serial, "api": 35,
        "build_evidence": str(build), "apk": str(apk), "apk_sha256": hashlib.sha256(apk.read_bytes()).hexdigest(),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "verdict": "INSTALLED_AND_LAUNCH_REQUESTED_NOT_VISUALLY_VERIFIED",
        "pending": ["actual UI visible", "app startup without crash", "B01-B05 real sources and reader"],
    }
    (evidence / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] Pedido de abertura enviado no AVD. Evidencia: {evidence}")
    print("Confira visualmente a janela Android; esta etapa NAO certifica A01/A02 nem leitura real.")
    return evidence


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("baseline", "spike001"))
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--consent", action="store_true", help="explicit user confirmation from the main CMD")
    args = parser.parse_args(argv)
    if not args.consent:
        print("[INTERROMPIDO] Use as opcoes 8/9 do CMD e confirme a instalacao no AVD.", file=sys.stderr)
        return 3
    try:
        workspace = args.workspace.expanduser().resolve()
        packages, build = find_apks(workspace)
        sdk = sdk_location()
        adb, serial = ensure_avd(workspace, sdk)
        install_and_launch(adb, serial, packages[args.stage], args.stage, workspace, build)
        return 0
    except EmulatorError as exc:
        print("[ERRO EMULADOR]", exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
