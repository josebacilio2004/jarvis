package com.starkindustries.jarvis;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.graphics.Bitmap;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.PowerManager;
import android.os.Vibrator;
import android.os.VibrationEffect;
import android.hardware.camera2.CameraManager;
import android.provider.AlarmClock;
import android.provider.ContactsContract;
import android.view.View;
import android.webkit.JavascriptInterface;
import android.webkit.PermissionRequest;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.EditText;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.app.NotificationCompat;
import androidx.core.app.NotificationManagerCompat;
import androidx.core.content.ContextCompat;
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout;

import java.text.Normalizer;
import java.util.ArrayList;
import java.util.List;

public class MainActivity extends AppCompatActivity {

    private static final String PREFS_NAME = "JarvisPrefs";
    private static final String KEY_SERVER_URL = "server_url";
    private static final int PERMISSION_REQUEST_CODE = 101;
    private static final String CHANNEL_ID = "jarvis_media_channel";
    private static final int NOTIFICATION_ID = 1001;

    private BackgroundAudioWebView webView;
    private SwipeRefreshLayout swipeRefresh;
    private SharedPreferences prefs;
    private PowerManager.WakeLock wakeLock;

    public class StarkAndroidBridge {
        private final Context mContext;

        public StarkAndroidBridge(Context context) {
            this.mContext = context;
        }

        @JavascriptInterface
        public void makePhoneCall(String target) {
            runOnUiThread(() -> {
                try {
                    String cleanTarget = (target == null) ? "" : target.trim();
                    if (cleanTarget.isEmpty()) {
                        Toast.makeText(mContext, "Destinatario no especificado", Toast.LENGTH_SHORT).show();
                        return;
                    }

                    // 1. Resolve Contact Name to actual Phone Number
                    String resolvedNumber = resolvePhoneNumber(cleanTarget);
                    String numberToCall = (resolvedNumber != null && !resolvedNumber.isEmpty()) ? resolvedNumber : cleanTarget;

                    // Clean string to phone digits and plus symbol
                    String dialString = numberToCall.replaceAll("[^0-9+]", "");
                    if (dialString.isEmpty()) {
                        dialString = numberToCall;
                    }

                    // 2. Perform direct phone call if permitted, else dialer
                    Intent callIntent;
                    if (ContextCompat.checkSelfPermission(mContext, Manifest.permission.CALL_PHONE) == PackageManager.PERMISSION_GRANTED) {
                        callIntent = new Intent(Intent.ACTION_CALL);
                    } else {
                        callIntent = new Intent(Intent.ACTION_DIAL);
                    }

                    callIntent.setData(Uri.parse("tel:" + Uri.encode(dialString)));
                    callIntent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                    mContext.startActivity(callIntent);

                    String msg = (resolvedNumber != null) 
                            ? "Marcando a " + cleanTarget + " (" + resolvedNumber + ")" 
                            : "Marcando a " + cleanTarget;
                    Toast.makeText(mContext, msg, Toast.LENGTH_SHORT).show();

                } catch (Exception e) {
                    Toast.makeText(mContext, "Error al enlazar llamada: " + e.getMessage(), Toast.LENGTH_LONG).show();
                }
            });
        }

        @JavascriptInterface
        public void showMediaNotification(String title, String subtitle) {
            MainActivity.this.showMediaNotification(title, subtitle);
        }

        @JavascriptInterface
        public void cancelMediaNotification() {
            MainActivity.this.cancelMediaNotification();
        }

        @JavascriptInterface
        public void openBrowser(String url) {
            runOnUiThread(() -> {
                try {
                    Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
                    intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                    mContext.startActivity(intent);
                } catch (Exception e) {
                    Toast.makeText(mContext, "Error al abrir enlace: " + e.getMessage(), Toast.LENGTH_SHORT).show();
                }
            });
        }

        @JavascriptInterface
        public void setAlarm(int hour, int minute, String message) {
            runOnUiThread(() -> {
                try {
                    Intent intent = new Intent(AlarmClock.ACTION_SET_ALARM);
                    intent.putExtra(AlarmClock.EXTRA_HOUR, hour);
                    intent.putExtra(AlarmClock.EXTRA_MINUTES, minute);
                    intent.putExtra(AlarmClock.EXTRA_MESSAGE, (message != null && !message.isEmpty()) ? message : "Alarma J.A.R.V.I.S.");
                    intent.putExtra(AlarmClock.EXTRA_SKIP_UI, false);
                    intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                    mContext.startActivity(intent);
                    Toast.makeText(mContext, "Alarma programada a las " + String.format("%02d:%02d", hour, minute), Toast.LENGTH_SHORT).show();
                } catch (Exception e) {
                    Toast.makeText(mContext, "Error al programar alarma: " + e.getMessage(), Toast.LENGTH_SHORT).show();
                }
            });
        }

        @JavascriptInterface
        public void setTimer(int seconds, String message) {
            runOnUiThread(() -> {
                try {
                    Intent intent = new Intent(AlarmClock.ACTION_SET_TIMER);
                    intent.putExtra(AlarmClock.EXTRA_LENGTH, seconds);
                    intent.putExtra(AlarmClock.EXTRA_MESSAGE, (message != null && !message.isEmpty()) ? message : "Temporizador J.A.R.V.I.S.");
                    intent.putExtra(AlarmClock.EXTRA_SKIP_UI, false);
                    intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                    mContext.startActivity(intent);
                    Toast.makeText(mContext, "Temporizador de " + seconds + " seg activado", Toast.LENGTH_SHORT).show();
                } catch (Exception e) {
                    Toast.makeText(mContext, "Error al iniciar temporizador: " + e.getMessage(), Toast.LENGTH_SHORT).show();
                }
            });
        }

        @JavascriptInterface
        public void toggleFlashlight(boolean enable) {
            runOnUiThread(() -> {
                try {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                        CameraManager cm = (CameraManager) getSystemService(Context.CAMERA_SERVICE);
                        if (cm != null) {
                            String cameraId = cm.getCameraIdList()[0];
                            cm.setTorchMode(cameraId, enable);
                            Toast.makeText(mContext, enable ? "Linterna activada" : "Linterna desactivada", Toast.LENGTH_SHORT).show();
                        }
                    }
                } catch (Exception e) {
                    Toast.makeText(mContext, "Error linterna: " + e.getMessage(), Toast.LENGTH_SHORT).show();
                }
            });
        }

        @JavascriptInterface
        public void vibratePhone(int milliseconds) {
            runOnUiThread(() -> {
                try {
                    Vibrator v = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);
                    if (v != null && v.hasVibrator()) {
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                            v.vibrate(VibrationEffect.createOneShot(milliseconds > 0 ? milliseconds : 200, VibrationEffect.DEFAULT_AMPLITUDE));
                        } else {
                            v.vibrate(milliseconds > 0 ? milliseconds : 200);
                        }
                    }
                } catch (Exception e) {}
            });
        }

        @JavascriptInterface
        public void openMaps(String location) {
            runOnUiThread(() -> {
                try {
                    Uri gmmIntentUri = Uri.parse("geo:0,0?q=" + Uri.encode(location));
                    Intent mapIntent = new Intent(Intent.ACTION_VIEW, gmmIntentUri);
                    mapIntent.setPackage("com.google.android.apps.maps");
                    mapIntent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                    if (mapIntent.resolveActivity(getPackageManager()) != null) {
                        startActivity(mapIntent);
                    } else {
                        Intent genericMap = new Intent(Intent.ACTION_VIEW, Uri.parse("https://www.google.com/maps/search/?api=1&query=" + Uri.encode(location)));
                        genericMap.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                        startActivity(genericMap);
                    }
                } catch (Exception e) {
                    Toast.makeText(mContext, "Error al abrir mapas: " + e.getMessage(), Toast.LENGTH_SHORT).show();
                }
            });
        }

        @JavascriptInterface
        public boolean isNativeApp() {
            return true;
        }
    }

    private String normalizeString(String input) {
        if (input == null) return "";
        return Normalizer.normalize(input, Normalizer.Form.NFD)
                .replaceAll("\\p{InCombiningDiacriticalMarks}+", "")
                .toLowerCase()
                .trim();
    }

    private String resolvePhoneNumber(String target) {
        if (target == null || target.trim().isEmpty()) return null;
        String cleanTarget = target.trim();

        // If it's already digits, return as-is
        if (cleanTarget.matches("^[+]?[0-9\\s-]{6,}$")) {
            return cleanTarget;
        }

        if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_CONTACTS) != PackageManager.PERMISSION_GRANTED) {
            return null;
        }

        String searchNormalized = normalizeString(cleanTarget);
        Uri uri = ContactsContract.CommonDataKinds.Phone.CONTENT_URI;
        String[] projection = new String[]{
                ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME,
                ContactsContract.CommonDataKinds.Phone.NUMBER
        };

        Cursor cursor = null;
        try {
            cursor = getContentResolver().query(uri, projection, null, null, null);
            if (cursor != null) {
                String partialMatchNumber = null;
                while (cursor.moveToNext()) {
                    int nameIdx = cursor.getColumnIndex(ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME);
                    int numIdx = cursor.getColumnIndex(ContactsContract.CommonDataKinds.Phone.NUMBER);
                    if (nameIdx >= 0 && numIdx >= 0) {
                        String name = cursor.getString(nameIdx);
                        String number = cursor.getString(numIdx);
                        if (name != null && number != null) {
                            String normName = normalizeString(name);
                            // Exact match (e.g. "mama" == "mama")
                            if (normName.equals(searchNormalized)) {
                                return number;
                            }
                            // Starts with or contains match fallback
                            if (normName.contains(searchNormalized) && partialMatchNumber == null) {
                                partialMatchNumber = number;
                            }
                        }
                    }
                }
                if (partialMatchNumber != null) {
                    return partialMatchNumber;
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            if (cursor != null) cursor.close();
        }
        return null;
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            CharSequence name = "J.A.R.V.I.S. Audio & Tareas";
            String description = "Notificaciones de reproducción y operaciones de Stark Industries";
            int importance = NotificationManager.IMPORTANCE_LOW;
            NotificationChannel channel = new NotificationChannel(CHANNEL_ID, name, importance);
            channel.setDescription(description);
            NotificationManager nm = getSystemService(NotificationManager.class);
            if (nm != null) {
                nm.createNotificationChannel(channel);
            }
        }
    }

    public void showMediaNotification(String title, String subtitle) {
        runOnUiThread(() -> {
            try {
                createNotificationChannel();
                Intent intent = new Intent(this, MainActivity.class);
                intent.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
                PendingIntent pendingIntent = PendingIntent.getActivity(this, 0, intent,
                        PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

                String mainTitle = (title != null && !title.isEmpty()) ? title : "J.A.R.V.I.S. OS";
                String mainSub = (subtitle != null && !subtitle.isEmpty()) ? subtitle : "Transmisión Stark Activa";

                NotificationCompat.Builder builder = new NotificationCompat.Builder(this, CHANNEL_ID)
                        .setSmallIcon(R.mipmap.ic_launcher)
                        .setContentTitle(mainTitle)
                        .setContentText(mainSub)
                        .setSubText("J.A.R.V.I.S. AUDIO")
                        .setPriority(NotificationCompat.PRIORITY_LOW)
                        .setContentIntent(pendingIntent)
                        .setOngoing(true)
                        .setAutoCancel(false);

                NotificationManagerCompat manager = NotificationManagerCompat.from(this);
                if (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU ||
                        ActivityCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED) {
                    manager.notify(NOTIFICATION_ID, builder.build());
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        });
    }

    public void cancelMediaNotification() {
        runOnUiThread(() -> {
            try {
                NotificationManagerCompat manager = NotificationManagerCompat.from(this);
                manager.cancel(NOTIFICATION_ID);
            } catch (Exception e) {
                e.printStackTrace();
            }
        });
    }

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);

        webView = findViewById(R.id.jarvisWebView);
        webView.setBackgroundColor(0xFF0A151B);
        swipeRefresh = findViewById(R.id.swipeRefresh);

        // Keep CPU awake for uninterrupted background audio playback
        try {
            PowerManager pm = (PowerManager) getSystemService(Context.POWER_SERVICE);
            if (pm != null) {
                wakeLock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "Jarvis::AudioBackgroundPlayback");
                wakeLock.acquire(60 * 60 * 1000L /* 60 min */);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }

        // Configure Swipe to Refresh
        swipeRefresh.setColorSchemeColors(0xFF00DAF3, 0xFFFF2A44);
        swipeRefresh.setProgressBackgroundColorSchemeColor(0xFF0A151B);
        swipeRefresh.setOnRefreshListener(() -> webView.reload());

        // Configure WebView
        WebSettings ws = webView.getSettings();
        ws.setJavaScriptEnabled(true);
        ws.setDomStorageEnabled(true);
        ws.setDatabaseEnabled(true);
        ws.setAllowFileAccess(true);
        ws.setMediaPlaybackRequiresUserGesture(false);
        ws.setUseWideViewPort(true);
        ws.setLoadWithOverviewMode(true);
        ws.setSupportZoom(false);
        ws.setBuiltInZoomControls(false);

        // Register Native JavaScript Bridge for Phone Calling & Media Notifications
        webView.addJavascriptInterface(new StarkAndroidBridge(this), "AndroidBridge");

        // Enable Mixed Content for local/remote hybrid connections
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            ws.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        }

        // WebChromeClient to auto-grant Microphone and Speech permissions
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onPermissionRequest(final PermissionRequest request) {
                runOnUiThread(() -> {
                    // Automatically grant audio capture to Stark HUD
                    request.grant(request.getResources());
                });
            }
        });

        // WebViewClient to handle page lifecycle and native intent links (tel:, mailto:)
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageStarted(WebView view, String url, Bitmap favicon) {
                swipeRefresh.setRefreshing(true);
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                swipeRefresh.setRefreshing(false);
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                String url = request.getUrl().toString();
                if (url.startsWith("tel:") || url.startsWith("mailto:") || url.startsWith("sms:") || url.startsWith("intent:") ||
                    url.contains("youtube.com") || url.contains("youtu.be")) {
                    try {
                        Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
                        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                        startActivity(intent);
                        return true;
                    } catch (Exception e) {
                        return false;
                    }
                }
                return false;
            }

            private void handleLoadError(WebView view) {
                swipeRefresh.setRefreshing(false);
                String offlineHtml = "<html><body style='background:#0a151b;color:#00daf3;font-family:sans-serif;display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;margin:0;padding:24px;text-align:center;box-sizing:border-box;'>"
                        + "<div style='font-size:36px;margin-bottom:12px;'>⚠️</div>"
                        + "<h2 style='color:#ff2a44;margin:0 0 12px 0;letter-spacing:1px;font-size:18px;'>[ENLACE DESCONECTADO]</h2>"
                        + "<p style='color:#d9e4ed;font-size:13px;line-height:1.6;margin:0 0 16px 0;'>No se pudo conectar a:<br><strong style='color:#00daf3;word-break:break-all;'>" + getServerUrl() + "</strong></p>"
                        + "<p style='color:#849396;font-size:12px;margin:0 0 24px 0;line-height:1.5;'>Asegúrese de que el servidor est&eacute; iniciado con <code>python app.py</code> y que su tel&eacute;fono est&eacute; en la misma red Wi-Fi (o use su URL de Render).</p>"
                        + "<button onclick='location.reload()' style='background:#00daf3;color:#000;border:none;padding:12px 24px;font-weight:bold;font-size:13px;border-radius:4px;cursor:pointer;margin-bottom:14px;box-shadow:0 0 15px rgba(0,218,243,0.4);'>REINTENTAR ENLACE</button>"
                        + "<p style='color:#555;font-size:11px;margin-top:10px;'>Mantenga presionada la pantalla para cambiar la IP o ingresar la URL de Render.</p>"
                        + "</body></html>";
                view.loadDataWithBaseURL(null, offlineHtml, "text/html", "utf-8", null);
                showConnectionErrorDialog();
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) {
                    handleLoadError(view);
                }
            }

            @SuppressWarnings("deprecation")
            @Override
            public void onReceivedError(WebView view, int errorCode, String description, String failingUrl) {
                handleLoadError(view);
            }
        });

        // Long press anywhere to configure server URL
        webView.setOnLongClickListener(v -> {
            showServerConfigDialog();
            return true;
        });

        // Request runtime permissions (Microphone, Phone, Contacts, Notifications)
        checkAndRequestPermissions();

        // Load the JARVIS server URL
        loadJarvisServer();
    }

    private void checkAndRequestPermissions() {
        List<String> permissions = new ArrayList<>();
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            permissions.add(Manifest.permission.RECORD_AUDIO);
        }
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CALL_PHONE) != PackageManager.PERMISSION_GRANTED) {
            permissions.add(Manifest.permission.CALL_PHONE);
        }
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_CONTACTS) != PackageManager.PERMISSION_GRANTED) {
            permissions.add(Manifest.permission.READ_CONTACTS);
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                permissions.add(Manifest.permission.POST_NOTIFICATIONS);
            }
        }
        if (!permissions.isEmpty()) {
            ActivityCompat.requestPermissions(this, permissions.toArray(new String[0]), PERMISSION_REQUEST_CODE);
        }
    }

    private String getServerUrl() {
        return prefs.getString(KEY_SERVER_URL, getString(R.string.default_server_url));
    }

    private void loadJarvisServer() {
        String url = getServerUrl();
        webView.loadUrl(url);
    }

    private void showServerConfigDialog() {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("J.A.R.V.I.S. Core Network");
        builder.setMessage("Configure la dirección IP o URL del servidor Stark (local o nube Render):");

        final EditText input = new EditText(this);
        input.setText(getServerUrl());
        input.setSelection(input.getText().length());
        builder.setView(input);

        builder.setPositiveButton("Conectar", (dialog, which) -> {
            String newUrl = input.getText().toString().trim();
            if (!newUrl.startsWith("http://") && !newUrl.startsWith("https://")) {
                newUrl = "http://" + newUrl;
            }
            prefs.edit().putString(KEY_SERVER_URL, newUrl).apply();
            webView.loadUrl(newUrl);
            Toast.makeText(MainActivity.this, "Sincronizando con " + newUrl, Toast.LENGTH_SHORT).show();
        });

        builder.setNegativeButton("Cancelar", (dialog, which) -> dialog.cancel());
        builder.show();
    }

    private void showConnectionErrorDialog() {
        new AlertDialog.Builder(this)
                .setTitle("Conexión Interrumpida")
                .setMessage("No se pudo establecer enlace con el servidor en " + getServerUrl() + ".\n\nVerifique si JARVIS está activo localmente en su PC o en Render.")
                .setPositiveButton("Reintentar", (dialog, which) -> webView.reload())
                .setNeutralButton("Cambiar URL/IP", (dialog, which) -> showServerConfigDialog())
                .setCancelable(false)
                .show();
    }

    @Override
    protected void onPause() {
        super.onPause();
        // Crucial: Do not suspend webView or pause timers so audio and network remain alive
    }

    @Override
    protected void onDestroy() {
        cancelMediaNotification();
        if (wakeLock != null && wakeLock.isHeld()) {
            wakeLock.release();
        }
        super.onDestroy();
    }

    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
