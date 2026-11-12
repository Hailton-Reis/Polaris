package test.polaris.isolation.probe;

import android.app.Activity;
import android.app.Instrumentation;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.ServiceConnection;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.os.IBinder;
import android.os.Parcel;
import android.os.Process;
import org.json.JSONObject;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.net.ServerSocket;
import java.net.SocketTimeoutException;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

/** Component proof only: no third-party APK, source adapter, broker, wizard or reader is integrated. */
public final class Probe extends Instrumentation {
    private void require(boolean condition, String message) { if (!condition) throw new AssertionError(message); }
    @Override public void onCreate(Bundle arguments) { super.onCreate(arguments); start(); }
    @Override public void onStart() {
        Bundle output = new Bundle();
        Context context = getTargetContext();
        final IBinder[] worker = new IBinder[1];
        CountDownLatch connected = new CountDownLatch(1);
        ServiceConnection connection = new ServiceConnection() {
            public void onServiceConnected(ComponentName name, IBinder service) { worker[0] = service; connected.countDown(); }
            public void onServiceDisconnected(ComponentName name) {}
        };
        boolean bound = false;
        try (ServerSocket listener = new ServerSocket(0)) {
            listener.setSoTimeout(500);
            File secret = new File(context.getFilesDir(), "host-only-secret.txt");
            File canary = new File(context.getFilesDir(), "host-only-canary.bin");
            try (FileOutputStream out = new FileOutputStream(secret)) { out.write("synthetic private test data".getBytes("UTF-8")); }
            try (FileOutputStream out = new FileOutputStream(canary)) { out.write(17); }
            bound = context.bindService(new Intent(context, IsolationService.class), connection, Context.BIND_AUTO_CREATE);
            require(bound && connected.await(30, TimeUnit.SECONDS), "Isolated service did not bind");
            JSONObject result;
            Parcel request = Parcel.obtain(); Parcel reply = Parcel.obtain();
            try {
                request.writeInterfaceToken("PolarisIsolationProbe");
                request.writeString(secret.getAbsolutePath()); request.writeString(canary.getAbsolutePath()); request.writeInt(listener.getLocalPort());
                require(worker[0].transact(1,request,reply,0), "Missing probe endpoint");
                reply.readException(); result = new JSONObject(reply.readString());
            } finally { request.recycle(); reply.recycle(); }
            require(result.getInt("worker_uid") != Process.myUid(), "Worker shares the host UID");
            require(context.checkPermission("android.permission.INTERNET",Process.myPid(),Process.myUid()) == PackageManager.PERMISSION_GRANTED,
                "Host internet permission missing; test would be inconclusive");
            require(result.getInt("internet_permission") == PackageManager.PERMISSION_DENIED,"Worker inherited host permission");
            require(!result.getBoolean("host_secret_read"),"Worker read host private data");
            try (FileInputStream in = new FileInputStream(canary)) {
                require(!result.getBoolean("host_canary_written") && in.read()==17 && in.read()==-1,"Worker modified the host canary");
            }
            require(!result.getBoolean("direct_network_connected"),"Worker connected without the network broker");
            try { listener.accept().close(); throw new AssertionError("Unexpected network connection reached host listener"); }
            catch (SocketTimeoutException expected) {}
            boolean rejected = false;
            request=Parcel.obtain();reply=Parcel.obtain();
            try {
                request.writeInterfaceToken("PolarisIsolationProbe");worker[0].transact(99,request,reply,0);
                try {reply.readException();} catch (SecurityException expected) {rejected=true;}
            } finally { request.recycle(); reply.recycle(); }
            require(rejected,"Unexpected IPC operation was accepted");
            result.put("host_uid",Process.myUid());result.put("api",android.os.Build.VERSION.SDK_INT);
            result.put("passed_checks",6);result.put("status","PASS");
            result.put("scope","Android isolation component proof; NOT an integrated extension sandbox");
            output.putString("result",result.toString());
            finish(Activity.RESULT_OK,output);
        } catch (Throwable failure) {
            output.putString("failure",failure.toString());finish(Activity.RESULT_CANCELED,output);
        } finally { if(bound) context.unbindService(connection); }
    }
}
