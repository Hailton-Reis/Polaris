#!/usr/bin/env python3
"""Headless software Android session with a file-backed ADB queue.

Keeps emulator, ADB and the managed network proxy in one execution session.
Requests are JSON files in SESSION/requests; results go to SESSION/results.
Each request contains an ADB args array, optional timeout and output filename.
This harness records execution; it does not declare runtime acceptance PASS.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.parse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sdk", required=True)
    parser.add_argument("--avd", required=True)
    parser.add_argument("--session", required=True)
    parser.add_argument("--timeout-multiplier", type=int, default=1)
    parser.add_argument("--cores", type=int, default=1)
    parser.add_argument("--gpu", choices=("swiftshader", "swangle", "software"), default="swiftshader")
    parser.add_argument("--max-seconds", type=int, default=1800)
    parser.add_argument("--source-network-only", action="store_true")
    parser.add_argument("--allow-host", action="append", default=[])
    options = parser.parse_args()
    if options.timeout_multiplier < 1 or options.cores < 1 or options.max_seconds < 1:
        parser.error("timeout-multiplier, cores and max-seconds must be positive")
    sdk = Path(options.sdk).resolve()
    root = Path(options.session).resolve()
    for name in ("requests", "results"):
        (root / name).mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, ANDROID_SDK_ROOT=str(sdk), ANDROID_HOME=str(sdk))
    source_proxy = None
    if options.source_network_only:
        if not options.allow_host:
            parser.error("source-network-only requires explicit allow-host entries")
        from emulator_source_proxy import start_proxy
        source_proxy = start_proxy(os.environ.get("HTTP_PROXY", ""), options.allow_host,
                                   root / "source-proxy.jsonl")
        bounded_url = f"http://127.0.0.1:{source_proxy.server_port}"
        for key in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
            env[key] = bounded_url
        # Emulator control/gRPC services stay on host loopback; external
        # destinations must use the filtering proxy.
        env["NO_PROXY"] = env["no_proxy"] = "localhost,127.0.0.1"
    command = [str(sdk / "emulator/emulator"), "-avd", options.avd,
               "-no-window", "-no-audio", "-no-boot-anim", "-no-snapshot", "-no-metrics",
               "-accel", "off", "-gpu", options.gpu, "-feature", "-Vulkan", "-memory", "2048",
               "-cores", str(options.cores), "-writable-system", "-port", "5554"]
    if env.get("HTTP_PROXY"):
        command += ["-http-proxy", env["HTTP_PROXY"]]
    if source_proxy:
        command += ["-dns-server", "127.0.0.1"]
    proxy = urllib.parse.urlsplit(env.get("HTTP_PROXY", ""))
    guest_proxy = f"10.0.2.2:{proxy.port}" if proxy.hostname in ("127.0.0.1", "localhost") else None
    adb = [str(sdk / "platform-tools/adb"), "-s", "emulator-5554"]
    start = time.monotonic()
    with (root / "emulator.log").open("wb") as log:
        emulator = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=env)
        print(f"Emulator started; PID={emulator.pid}; software CPU/GPU", flush=True)
        try:
            last_boot_check = 0.0
            booted = False
            timeout_applied = options.timeout_multiplier == 1
            proxy_applied = guest_proxy is None
            egress_applied = source_proxy is None
            while (emulator.poll() is None and not (root / "STOP").exists()
                   and time.monotonic() - start < options.max_seconds):
                now = time.monotonic()
                if now - last_boot_check > 15:
                    last_boot_check = now
                    try:
                        check = subprocess.run(adb + ["shell", "getprop", "sys.boot_completed"],
                                               capture_output=True, timeout=8, env=env)
                        booted = check.stdout.strip() == b"1"
                        if check.returncode == 0 and (not timeout_applied or not egress_applied):
                            # Emulator 37 ignores non-qemu.* -prop values. Apply this
                            # Android 12+ diagnostic property before restarting Java
                            # services, so Build/Watchdog read it on initialization.
                            subprocess.run(adb + ["root"], capture_output=True, timeout=15, env=env)
                            subprocess.run(adb + ["wait-for-device"], capture_output=True, timeout=20, env=env)
                            if source_proxy and not egress_applied:
                                # Deny guest direct TCP/UDP; only the local source
                                # proxy, guest loopback and ADB replies may leave.
                                port = source_proxy.server_port
                                firewall = (
                                    "iptables -N POLARIS_SOURCE_ONLY 2>/dev/null; "
                                    "iptables -F POLARIS_SOURCE_ONLY && "
                                    "iptables -A POLARIS_SOURCE_ONLY -o lo -j ACCEPT && "
                                    f"iptables -A POLARIS_SOURCE_ONLY -d 10.0.2.2 -p tcp --dport {port} -j ACCEPT && "
                                    "iptables -A POLARIS_SOURCE_ONLY -d 10.0.2.2 -p tcp --sport 5555 -j ACCEPT && "
                                    "iptables -A POLARIS_SOURCE_ONLY -j REJECT && "
                                    "(iptables -C OUTPUT -j POLARIS_SOURCE_ONLY 2>/dev/null || iptables -I OUTPUT 1 -j POLARIS_SOURCE_ONLY) && "
                                    "(ip6tables -N POLARIS_SOURCE_ONLY 2>/dev/null || true) && "
                                    "ip6tables -F POLARIS_SOURCE_ONLY && "
                                    "ip6tables -A POLARIS_SOURCE_ONLY -o lo -j ACCEPT && "
                                    "ip6tables -A POLARIS_SOURCE_ONLY -j REJECT && "
                                    "(ip6tables -C OUTPUT -j POLARIS_SOURCE_ONLY 2>/dev/null || ip6tables -I OUTPUT 1 -j POLARIS_SOURCE_ONLY)"
                                )
                                setup = subprocess.run(adb + ["shell", firewall], capture_output=True, timeout=30, env=env)
                                (root / "egress-setup.json").write_text(json.dumps({
                                    "returncode": setup.returncode,
                                    "stderr": setup.stderr.decode(errors="replace"),
                                    "allowed_hosts": options.allow_host,
                                }, indent=2) + "\n")
                                if setup.returncode != 0:
                                    raise RuntimeError("Guest egress restriction failed; stop before app execution")
                                egress_applied = True
                            multiplier = options.timeout_multiplier
                            setup = subprocess.run(adb + ["shell",
                                f"setprop ro.hw_timeout_multiplier {multiplier}; "
                                f"test \"$(getprop ro.hw_timeout_multiplier)\" = {multiplier} "
                                "&& stop && sleep 2 && start"],
                                capture_output=True, timeout=30, env=env)
                            (root / "timeout-setup.json").write_text(json.dumps({
                                "returncode": setup.returncode,
                                "stdout": setup.stdout.decode(errors="replace"),
                                "stderr": setup.stderr.decode(errors="replace"),
                                "multiplier": multiplier,
                            }, indent=2) + "\n")
                            timeout_applied = setup.returncode == 0
                            booted = False
                        if check.returncode == 0 and timeout_applied and not proxy_applied:
                            # A host HTTP proxy does not provide guest UDP DNS.
                            # Android's explicit proxy sends source hostnames in CONNECT.
                            setup = subprocess.run(adb + ["shell",
                                f"settings put global http_proxy {guest_proxy}; "
                                "settings put global captive_portal_mode 0; "
                                "settings get global http_proxy"],
                                capture_output=True, timeout=20, env=env)
                            proxy_applied = setup.returncode == 0 and setup.stdout.strip().decode() == guest_proxy
                            (root / "proxy-setup.json").write_text(json.dumps({
                                "returncode": setup.returncode, "configured": proxy_applied,
                                "stderr": setup.stderr.decode(errors="replace"),
                            }, indent=2) + "\n")
                    except subprocess.TimeoutExpired:
                        booted = False
                    state = {"boot_completed": booted, "elapsed_seconds": round(now - start)}
                    (root / "status.json").write_text(json.dumps(state) + "\n")
                    if booted and not (root / "BOOTED").exists():
                        (root / "BOOTED").write_text("Android sys.boot_completed=1\n")
                        print("Android boot completed", flush=True)
                for request in sorted((root / "requests").glob("*.json")):
                    if (root / "STOP").exists() or time.monotonic() - start >= options.max_seconds:
                        break
                    result_path = root / "results" / request.name
                    if result_path.exists():
                        continue
                    try:
                        data = json.loads(request.read_text())
                        # Package/settings binder services can appear before their
                        # internal dependencies finish initialization. Installing
                        # then can throw StorageManagerService.freeStorage NPEs.
                        if not booted and not data.get("allow_before_boot", False):
                            continue
                        args = data["args"]
                        if not isinstance(args, list) or not all(isinstance(x, str) for x in args):
                            raise ValueError("args must be an array of strings")
                        (root / "in-progress.json").write_text(json.dumps({
                            "request": request.name, "started_at": time.time(),
                        }) + "\n")
                        remaining = max(1, options.max_seconds - (time.monotonic() - start))
                        output = subprocess.run(adb + args, capture_output=True,
                                                timeout=min(data.get("timeout", 60), remaining), env=env)
                        if "output" in data:
                            target = (root / data["output"]).resolve()
                            if root not in target.parents:
                                raise ValueError("Output must remain inside session directory")
                            target.parent.mkdir(parents=True, exist_ok=True)
                            target.write_bytes(output.stdout)
                        result = {"args": args, "returncode": output.returncode,
                                  "stdout": "[saved to file]" if "output" in data else output.stdout.decode(errors="replace"),
                                  "stderr": output.stderr.decode(errors="replace")}
                    except Exception as error:
                        result = {"error": str(error)}
                    result_path.write_text(json.dumps(result, indent=2) + "\n")
                    (root / "in-progress.json").unlink(missing_ok=True)
                    print(f"Completed {request.name}: {result.get('returncode', 'error')}", flush=True)
                time.sleep(1)
            print(f"Session stopping; emulator exit={emulator.poll()}", flush=True)
        finally:
            if emulator.poll() is None:
                try:
                    subprocess.run(adb + ["shell", "sync"], capture_output=True, timeout=10, env=env)
                except subprocess.TimeoutExpired:
                    pass
                emulator.terminate()
                try:
                    emulator.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    emulator.kill()
            (root / "exit.json").write_text(json.dumps({"exit_code": emulator.returncode}) + "\n")
            if source_proxy:
                source_proxy.shutdown()
                source_proxy.server_close()


if __name__ == "__main__":
    main()
