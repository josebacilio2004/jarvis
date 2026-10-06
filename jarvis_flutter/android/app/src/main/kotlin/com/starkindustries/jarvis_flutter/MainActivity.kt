package com.starkindustries.jarvis_flutter

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.BatteryManager
import android.os.Build
import android.provider.MediaStore
import androidx.core.app.NotificationCompat
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    private val CHANNEL = "com.starkindustries.jarvis/app_control"
    private val CALL_REQ_CODE = 200
    private val NOTIF_CHANNEL_ID = "jarvis_status_channel"
    private val NOTIF_ID = 1001

    private var pendingNumber: String? = null
    private var pendingResult: MethodChannel.Result? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        createNotificationChannel()

        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL).setMethodCallHandler { call, result ->
            when (call.method) {
                "minimizeApp" -> {
                    moveTaskToBack(true)
                    result.success(true)
                }
                "makeDirectCall" -> {
                    val rawNumber = call.argument<String>("number")
                    if (rawNumber.isNullOrBlank()) {
                        result.error("EMPTY_NUMBER", "Número de teléfono no especificado", null)
                        return@setMethodCallHandler
                    }
                    val cleanNumber = rawNumber.replace(" ", "")
                    if (checkSelfPermission(Manifest.permission.CALL_PHONE) == PackageManager.PERMISSION_GRANTED) {
                        dialDirect(cleanNumber)
                        result.success(true)
                    } else {
                        pendingNumber = cleanNumber
                        pendingResult = result
                        requestPermissions(arrayOf(Manifest.permission.CALL_PHONE), CALL_REQ_CODE)
                    }
                }
                "requestCallPermission" -> {
                    if (checkSelfPermission(Manifest.permission.CALL_PHONE) == PackageManager.PERMISSION_GRANTED) {
                        result.success(true)
                    } else {
                        requestPermissions(arrayOf(Manifest.permission.CALL_PHONE), CALL_REQ_CODE)
                        result.success(false)
                    }
                }
                "openCamera" -> {
                    try {
                        val cameraIntent = Intent(MediaStore.INTENT_ACTION_STILL_IMAGE_CAMERA).apply {
                            flags = Intent.FLAG_ACTIVITY_NEW_TASK
                        }
                        startActivity(cameraIntent)
                        result.success(true)
                    } catch (e: Exception) {
                        try {
                            val fallbackIntent = Intent(MediaStore.ACTION_IMAGE_CAPTURE).apply {
                                flags = Intent.FLAG_ACTIVITY_NEW_TASK
                            }
                            startActivity(fallbackIntent)
                            result.success(true)
                        } catch (e2: Exception) {
                            result.error("CAMERA_ERROR", "No se pudo abrir la cámara: ${e2.message}", null)
                        }
                    }
                }
                "getBatteryStatus" -> {
                    try {
                        val bm = getSystemService(Context.BATTERY_SERVICE) as BatteryManager
                        val level = bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
                        val status = bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_STATUS)
                        val isCharging = (status == BatteryManager.BATTERY_STATUS_CHARGING ||
                                          status == BatteryManager.BATTERY_STATUS_FULL)
                        result.success(mapOf("level" to level, "isCharging" to isCharging))
                    } catch (e: Exception) {
                        result.error("BATTERY_ERROR", e.message, null)
                    }
                }
                "showNotification" -> {
                    val title = call.argument<String>("title") ?: "J.A.R.V.I.S. OS"
                    val content = call.argument<String>("content") ?: "Sistemas activos"
                    val isPlaying = call.argument<Boolean>("isPlaying") ?: false
                    displayNotification(title, content, isPlaying)
                    result.success(true)
                }
                "cancelNotification" -> {
                    val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
                    manager.cancel(NOTIF_ID)
                    result.success(true)
                }
                else -> {
                    result.notImplemented()
                }
            }
        }
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val name = "J.A.R.V.I.S. Live Status"
            val descriptionText = "Notificaciones de estado y reproducción multimedia de J.A.R.V.I.S."
            val importance = NotificationManager.IMPORTANCE_LOW
            val channel = NotificationChannel(NOTIF_CHANNEL_ID, name, importance).apply {
                description = descriptionText
                setShowBadge(false)
            }
            val notificationManager: NotificationManager =
                getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            notificationManager.createNotificationChannel(channel)
        }
    }

    private fun displayNotification(title: String, content: String, isPlaying: Boolean) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 300)
                return
            }
        }

        val openIntent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            openIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val builder = NotificationCompat.Builder(this, NOTIF_CHANNEL_ID)
            .setSmallIcon(R.mipmap.ic_launcher)
            .setContentTitle(title)
            .setContentText(content)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .setContentIntent(pendingIntent)
            .setOngoing(isPlaying)
            .setAutoCancel(false)

        val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        notificationManager.notify(NOTIF_ID, builder.build())
    }

    private fun dialDirect(number: String) {
        val intent = Intent(Intent.ACTION_CALL, Uri.parse("tel:$number")).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK
        }
        startActivity(intent)
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == CALL_REQ_CODE) {
            if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                pendingNumber?.let { dialDirect(it) }
                pendingResult?.success(true)
            } else {
                pendingNumber?.let {
                    val dialIntent = Intent(Intent.ACTION_DIAL, Uri.parse("tel:$it")).apply {
                        flags = Intent.FLAG_ACTIVITY_NEW_TASK
                    }
                    startActivity(dialIntent)
                }
                pendingResult?.success(false)
            }
            pendingNumber = null
            pendingResult = null
        }
    }
}
