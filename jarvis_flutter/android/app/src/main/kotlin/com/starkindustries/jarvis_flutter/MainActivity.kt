package com.starkindustries.jarvis_flutter

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    private val CHANNEL = "com.starkindustries.jarvis/app_control"
    private val CALL_REQ_CODE = 200
    private var pendingNumber: String? = null
    private var pendingResult: MethodChannel.Result? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
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
                else -> {
                    result.notImplemented()
                }
            }
        }
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
