package com.starkindustries.jarvis;

import android.Manifest;
import android.annotation.SuppressLint;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.PowerManager;
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
import androidx.core.content.ContextCompat;
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout;

public class MainActivity extends AppCompatActivity {

    private static final String PREFS_NAME = "JarvisPrefs";
    private static final String KEY_SERVER_URL = "server_url";
    private static final int PERMISSION_REQUEST_CODE = 101;

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
                    Intent dialIntent = new Intent(Intent.ACTION_DIAL);
                    if (!cleanTarget.isEmpty()) {
                        dialIntent.setData(Uri.parse("tel:" + Uri.encode(cleanTarget)));
                    }
                    dialIntent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                    mContext.startActivity(dialIntent);
                    Toast.makeText(mContext, "Iniciando enlace telefónico: " + cleanTarget, Toast.LENGTH_SHORT).show();
                } catch (Exception e) {
                    Toast.makeText(mContext, "Error al marcar: " + e.getMessage(), Toast.LENGTH_SHORT).show();
                }
            });
        }

        @JavascriptInterface
        public void showToast(String msg) {
            runOnUiThread(() -> Toast.makeText(mContext, msg, Toast.LENGTH_SHORT).show());
        }

        @JavascriptInterface
        public boolean isNativeApp() {
            return true;
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);

        webView = findViewById(R.id.jarvisWebView);
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

        // Register Native JavaScript Bridge for Phone Calling & Native Actions
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
                if (url.startsWith("tel:") || url.startsWith("mailto:") || url.startsWith("sms:") || url.startsWith("intent:")) {
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

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                swipeRefresh.setRefreshing(false);
                if (request.isForMainFrame()) {
                    showConnectionErrorDialog();
                }
            }
        });

        // Long press anywhere to configure server URL
        webView.setOnLongClickListener(v -> {
            showServerConfigDialog();
            return true;
        });

        // Request runtime permissions (Microphone & Call Phone)
        checkAndRequestPermissions();

        // Load the JARVIS server URL
        loadJarvisServer();
    }

    private void checkAndRequestPermissions() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
                != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this,
                    new String[]{Manifest.permission.RECORD_AUDIO, Manifest.permission.CALL_PHONE},
                    PERMISSION_REQUEST_CODE);
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
        // Crucial: We intentionally do NOT call webView.onPause() or webView.pauseTimers()
        // so that background audio (yt-dlp stream / TTS voice) keeps streaming when minimized!
    }

    @Override
    protected void onDestroy() {
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
