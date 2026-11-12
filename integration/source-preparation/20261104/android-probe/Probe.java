package test.polaris.preparation.probe;
import android.app.Instrumentation;
import android.os.Bundle;
import eu.kanade.tachiyomi.extension.util.PrivateExtensionFiles;
import eu.kanade.tachiyomi.extension.util.PrivateExtensionSignature;
import java.io.*;
import java.nio.file.Files;
import java.util.*;
import kotlin.Unit;
public class Probe extends Instrumentation {
  @Override public void onCreate(Bundle args) { super.onCreate(args); start(); }
  @Override public void onStart() {
    Bundle report = new Bundle(); int passed = 0;
    File root = new File(getTargetContext().getCacheDir(), "polaris-component-controls"); root.mkdirs();
    try {
      File signed = copy("signed.apk", root), tampered = copy("tampered.apk", root);
      Set<String> keys = PrivateExtensionSignature.INSTANCE.verify(signed, android.os.Build.VERSION.SDK_INT);
      if (!keys.equals(Collections.singleton("5a7a06cb326b09d4c872f35c553d8a3b6278ca01b3f0c92f333f3e73c53c96b7"))) throw new AssertionError("signer mismatch");
      passed++;
      File target = new File(root, "working.ext"); Files.write(target.toPath(), "working".getBytes("UTF-8"));
      try {
        PrivateExtensionFiles.INSTANCE.replace(tampered, target, () -> Unit.INSTANCE, staged -> {
          PrivateExtensionSignature.INSTANCE.verify(staged, android.os.Build.VERSION.SDK_INT); return Unit.INSTANCE;
        });
        throw new AssertionError("tampered APK accepted");
      } catch (Exception expected) { if (!(expected instanceof IOException)) throw expected; }
      if (!new String(Files.readAllBytes(target.toPath()), "UTF-8").equals("working")) throw new AssertionError("old extension lost");
      passed++;
      try {
        PrivateExtensionSignature.INSTANCE.requireReviewedIdentity("wrong.package", keys.iterator().next(), "test.polaris.reviewed", keys);
        throw new AssertionError("wrong package accepted");
      } catch (Exception expected) { if (!(expected instanceof IOException)) throw expected; }
      try {
        PrivateExtensionSignature.INSTANCE.requireReviewedIdentity("test.polaris.reviewed", "0000000000000000000000000000000000000000000000000000000000000000", "test.polaris.reviewed", keys);
        throw new AssertionError("wrong certificate accepted");
      } catch (Exception expected) { if (!(expected instanceof IOException)) throw expected; }
      passed++;
      PrivateExtensionFiles.INSTANCE.replace(signed, target, () -> Unit.INSTANCE, staged -> {
        PrivateExtensionSignature.INSTANCE.verify(staged, android.os.Build.VERSION.SDK_INT); return Unit.INSTANCE;
      });
      if (!Arrays.equals(Files.readAllBytes(signed.toPath()), Files.readAllBytes(target.toPath())) || target.canWrite()) throw new AssertionError("atomic readonly replacement failed");
      passed++;
      report.putString("stream", "PASS: signed APK verification, tamper rejection preserving old extension, package/certificate pinning, readonly atomic replacement\n");
      report.putInt("passed_checks", passed); report.putInt("android_api", android.os.Build.VERSION.SDK_INT);
      finish(-1, report);
    } catch (Throwable failure) {
      StringWriter trace = new StringWriter(); failure.printStackTrace(new PrintWriter(trace));
      report.putString("stream", trace.toString()); report.putInt("passed_checks", passed); finish(0, report);
    } finally { File[] files = root.listFiles(); if (files != null) for (File f : files) { f.setWritable(true); f.delete(); } root.delete(); }
  }
  private File copy(String name, File root) throws IOException {
    File file = new File(root, name);
    try (InputStream input = getTargetContext().getAssets().open(name); OutputStream out = new FileOutputStream(file)) {
      byte[] buffer = new byte[8192]; int read; while ((read = input.read(buffer)) >= 0) out.write(buffer, 0, read);
    } return file;
  }
}
