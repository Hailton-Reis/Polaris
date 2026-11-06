package test.polaris.isolation.probe;

import android.app.Service;
import android.content.Intent;
import android.os.Binder;
import android.os.IBinder;
import android.os.Parcel;
import android.os.Process;
import org.json.JSONObject;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.net.InetSocketAddress;
import java.net.Socket;

/** Deliberately attempts prohibited operations in a real Android isolated UID. No reader code. */
public final class IsolationService extends Service {
    private final Binder endpoint = new Binder() {
        @Override protected boolean onTransact(int code, Parcel data, Parcel reply, int flags) {
            try {
                data.enforceInterface("PolarisIsolationProbe");
                if (code != 1 || data.dataAvail() > 8192) {
                    reply.writeException(new SecurityException("Unsupported probe command"));
                    return true;
                }
                String secret = data.readString();
                String canary = data.readString();
                int port = data.readInt();
                JSONObject result = new JSONObject();
                result.put("worker_uid", Process.myUid());
                result.put("internet_permission", checkPermission("android.permission.INTERNET", Process.myPid(), Process.myUid()));
                boolean read = false;
                try (FileInputStream in = new FileInputStream(secret)) { read = in.read() >= 0; } catch (Exception expected) {}
                result.put("host_secret_read", read);
                boolean write = false;
                try (FileOutputStream out = new FileOutputStream(canary)) { out.write(42); write = true; } catch (Exception expected) {}
                result.put("host_canary_written", write);
                boolean network = false;
                try (Socket socket = new Socket()) {
                    socket.connect(new InetSocketAddress("127.0.0.1", port), 1000);
                    network = true;
                } catch (Exception expected) {}
                result.put("direct_network_connected", network);
                reply.writeNoException();
                reply.writeString(result.toString());
                return true;
            } catch (Exception error) {
                reply.writeException(error);
                return true;
            }
        }
    };
    @Override public IBinder onBind(Intent intent) { return endpoint; }
}
