#!/usr/bin/env python3
"""Install the issue #2 debug-only ADB hook after applying Spike-001."""
from pathlib import Path
import shutil
import sys

repo = Path(sys.argv[1]).resolve()
root = Path(__file__).resolve().parents[2]
manifest = repo / "app/src/debug/AndroidManifest.xml"
text = manifest.read_text()
activity = "eu.kanade.tachiyomi.polaris.Spike001DebugActivity"
if activity in text:
    raise SystemExit("Debug hook already installed")
if text.count("    </application>") != 1:
    raise SystemExit("Unexpected debug manifest; refusing to alter it")
target = repo / "app/src/debug/java/eu/kanade/tachiyomi/polaris/Spike001DebugActivity.kt"
if target.exists():
    raise SystemExit("Refusing to overwrite debug hook source")
target.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(root / "integration/r001/debug/Spike001DebugActivity.kt", target)
manifest.write_text(text.replace("    </application>",
    f'        <activity android:name="{activity}" android:exported="true" ' 
    'android:permission="android.permission.DUMP" '
    'android:theme="@android:style/Theme.Material.Light.NoActionBar" />\n    </application>'))
print("ISSUE002_DEBUG_HOOK_APPLIED")
