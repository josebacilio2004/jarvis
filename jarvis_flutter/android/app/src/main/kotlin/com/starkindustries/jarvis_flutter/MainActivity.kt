package com.starkindustries.jarvis_flutter

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.ContentResolver
import android.content.ContentValues
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.BatteryManager
import android.os.Build
import android.os.Bundle
import android.provider.CalendarContract
import android.provider.ContactsContract
import android.provider.MediaStore
import android.provider.Settings
import android.telephony.TelephonyManager
import android.util.Log
import android.widget.Toast
import androidx.core.app.NotificationCompat
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import java.util.TimeZone

data class CalendarEventData(
    val title: String,
    val description: String?,
    val startTimeMs: Long,
    val endTimeMs: Long,
    val location: String?
)

class MainActivity : FlutterActivity() {
    private val CHANNEL = "com.starkindustries.jarvis/app_control"
    private val CALL_REQ_CODE = 200
    private val PERMISSIONS_REQ_CODE = 201
    private val CALENDAR_REQ_CODE = 202
    private val CONTACTS_REQ_CODE = 203
    private val NOTIF_CHANNEL_ID = "jarvis_status_channel"
    private val NOTIF_ID = 1001

    private var pendingNumber: String? = null
    private var pendingResult: MethodChannel.Result? = null
    private var pendingCalendarEvent: CalendarEventData? = null
    private var pendingWhatsAppCallTarget: String? = null
    private var pendingWhatsAppVideoCallTarget: String? = null
    private var pendingWhatsAppSendTarget: Pair<String, String>? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        createNotificationChannel()
        requestEssentialPermissions()

        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL).setMethodCallHandler { call, result ->
            when (call.method) {
                "minimizeApp" -> {
                    moveTaskToBack(true)
                    result.success(true)
                }
                "requestPermissions" -> {
                    requestEssentialPermissions()
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
                "sendWhatsApp" -> {
                    val target = call.argument<String>("target") ?: ""
                    val message = call.argument<String>("message") ?: ""
                    sendWhatsApp(target, message)
                    result.success(true)
                }
                "makeWhatsAppCall" -> {
                    val target = call.argument<String>("target") ?: ""
                    makeWhatsAppCall(target)
                    result.success(true)
                }
                "makeWhatsAppVideoCall" -> {
                    val target = call.argument<String>("target") ?: ""
                    makeWhatsAppVideoCall(target)
                    result.success(true)
                }
                "openAccessibilitySettings" -> {
                    openAccessibilitySettings()
                    result.success(true)
                }
                "isAccessibilityServiceEnabled" -> {
                    result.success(isAccessibilityServiceEnabled())
                }
                "addCalendarEvent" -> {
                    val title = call.argument<String>("title") ?: "Evento Stark"
                    val description = call.argument<String>("description")
                    val startTimeMs = (call.argument<Number>("startTimeMs"))?.toLong() ?: System.currentTimeMillis()
                    val endTimeMs = (call.argument<Number>("endTimeMs"))?.toLong() ?: (startTimeMs + 3600000L)
                    val location = call.argument<String>("location")
                    val ok = addCalendarEvent(title, description, startTimeMs, endTimeMs, location)
                    result.success(ok)
                }
                else -> {
                    result.notImplemented()
                }
            }
        }
    }

    private fun isAccessibilityServiceEnabled(): Boolean {
        if (JarvisAccessibilityService.isServiceActive) return true
        val enabledServices = Settings.Secure.getString(
            contentResolver,
            Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
        ) ?: return false
        return enabledServices.contains(packageName)
    }

    private fun openAccessibilitySettings() {
        try {
            val intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
            }
            startActivity(intent)
        } catch (e: Exception) {
            Log.e("JARVIS", "Failed to open accessibility settings: ${e.message}")
        }
    }

    private fun requestEssentialPermissions() {
        val permsToRequest = mutableListOf<String>()
        val permissions = arrayOf(
            Manifest.permission.READ_CONTACTS,
            Manifest.permission.READ_CALENDAR,
            Manifest.permission.WRITE_CALENDAR,
            Manifest.permission.CALL_PHONE,
            Manifest.permission.CAMERA
        )
        for (p in permissions) {
            if (checkSelfPermission(p) != PackageManager.PERMISSION_GRANTED) {
                permsToRequest.add(p)
            }
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                permsToRequest.add(Manifest.permission.POST_NOTIFICATIONS)
            }
        }
        if (permsToRequest.isNotEmpty()) {
            requestPermissions(permsToRequest.toTypedArray(), PERMISSIONS_REQ_CODE)
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
        when (requestCode) {
            CALL_REQ_CODE -> {
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
            CALENDAR_REQ_CODE -> {
                if (grantResults.isNotEmpty() && grantResults.all { it == PackageManager.PERMISSION_GRANTED }) {
                    pendingCalendarEvent?.let { evt ->
                        addCalendarEvent(evt.title, evt.description, evt.startTimeMs, evt.endTimeMs, evt.location)
                    }
                }
                pendingCalendarEvent = null
            }
            CONTACTS_REQ_CODE -> {
                if (grantResults.isNotEmpty() && grantResults.all { it == PackageManager.PERMISSION_GRANTED }) {
                    pendingWhatsAppCallTarget?.let { target ->
                        makeWhatsAppCall(target)
                    }
                    pendingWhatsAppVideoCallTarget?.let { target ->
                        makeWhatsAppVideoCall(target)
                    }
                    pendingWhatsAppSendTarget?.let { (target, msg) ->
                        sendWhatsApp(target, msg)
                    }
                }
                pendingWhatsAppCallTarget = null
                pendingWhatsAppVideoCallTarget = null
                pendingWhatsAppSendTarget = null
            }
            PERMISSIONS_REQ_CODE -> {
                Log.i("JARVIS", "Essential permissions result handled")
            }
        }
    }

    private fun getCountryCode(): String {
        try {
            val tm = getSystemService(Context.TELEPHONY_SERVICE) as? TelephonyManager
            val simCountry = tm?.simCountryIso?.lowercase()
            val networkCountry = tm?.networkCountryIso?.lowercase()
            val country = if (!simCountry.isNullOrBlank()) simCountry else if (!networkCountry.isNullOrBlank()) networkCountry else "pe"
            return when (country) {
                "pe" -> "51"
                "mx" -> "52"
                "co" -> "57"
                "ar" -> "54"
                "cl" -> "56"
                "ec" -> "593"
                "es" -> "34"
                "us" -> "1"
                else -> "51"
            }
        } catch (e: Exception) {
            return "51"
        }
    }

    private fun formatWhatsAppPhone(rawPhone: String): String {
        var digits = rawPhone.replace(Regex("[^0-9]"), "")
        if (digits.startsWith("00")) {
            digits = digits.substring(2)
        }
        val cc = getCountryCode()
        if (digits.length == 9 && (cc == "51" || digits.startsWith("9"))) {
            return "51$digits"
        }
        if (digits.length == 10 && cc == "52") {
            return "52$digits"
        }
        return digits
    }

    private fun resolvePhoneNumber(target: String): String? {
        val digits = target.replace(Regex("[^0-9+]"), "")
        if (digits.replace("+", "").length >= 7) {
            return formatWhatsAppPhone(digits)
        }
        if (checkSelfPermission(Manifest.permission.READ_CONTACTS) != PackageManager.PERMISSION_GRANTED) {
            return null
        }

        val trimmedTarget = target.trim()

        // 1. Fuzzy filter URI query (handles accents, aliases)
        try {
            val filterUri = Uri.withAppendedPath(
                ContactsContract.CommonDataKinds.Phone.CONTENT_FILTER_URI,
                Uri.encode(trimmedTarget)
            )
            contentResolver.query(
                filterUri,
                arrayOf(ContactsContract.CommonDataKinds.Phone.NUMBER),
                null, null, null
            )?.use { cursor ->
                if (cursor.moveToFirst()) {
                    val num = cursor.getString(0)
                    if (!num.isNullOrBlank()) return formatWhatsAppPhone(num)
                }
            }
        } catch (e: Exception) {
            Log.w("JARVIS", "CONTENT_FILTER_URI error: ${e.message}")
        }

        // 2. Query CommonDataKinds.Phone with DISPLAY_NAME LIKE
        try {
            val cursor = contentResolver.query(
                ContactsContract.CommonDataKinds.Phone.CONTENT_URI,
                arrayOf(ContactsContract.CommonDataKinds.Phone.NUMBER),
                "${ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME} LIKE ?",
                arrayOf("%$trimmedTarget%"),
                null
            )
            cursor?.use {
                if (it.moveToFirst()) {
                    val num = it.getString(0)
                    if (!num.isNullOrBlank()) return formatWhatsAppPhone(num)
                }
            }
        } catch (e: Exception) {
            Log.w("JARVIS", "DISPLAY_NAME LIKE error: ${e.message}")
        }

        // 3. Query ContactsContract.Data for WhatsApp profile row
        try {
            contentResolver.query(
                ContactsContract.Data.CONTENT_URI,
                arrayOf(ContactsContract.Data.DATA1),
                "${ContactsContract.Data.MIMETYPE} = ? AND ${ContactsContract.Data.DISPLAY_NAME} LIKE ?",
                arrayOf("vnd.android.cursor.item/vnd.com.whatsapp.profile", "%$trimmedTarget%"),
                null
            )?.use { cursor ->
                if (cursor.moveToFirst()) {
                    val jid = cursor.getString(0)
                    if (!jid.isNullOrBlank()) {
                        val d = jid.split("@")[0].replace(Regex("[^0-9]"), "")
                        if (d.length >= 7) return formatWhatsAppPhone(d)
                    }
                }
            }
        } catch (e: Exception) {
            Log.w("JARVIS", "WhatsApp profile data error: ${e.message}")
        }

        return null
    }

    private fun findWhatsAppVoipDataId(target: String, cleanPhone: String?): Long? {
        if (checkSelfPermission(Manifest.permission.READ_CONTACTS) != PackageManager.PERMISSION_GRANTED) {
            return null
        }

        val trimmedTarget = target.trim()

        // 1. Direct match on WhatsApp VoIP MIME type by DISPLAY_NAME
        try {
            contentResolver.query(
                ContactsContract.Data.CONTENT_URI,
                arrayOf(ContactsContract.Data._ID),
                "${ContactsContract.Data.MIMETYPE} = ? AND ${ContactsContract.Data.DISPLAY_NAME} LIKE ?",
                arrayOf("vnd.android.cursor.item/vnd.com.whatsapp.voip.call", "%$trimmedTarget%"),
                null
            )?.use { cursor ->
                if (cursor.moveToFirst()) {
                    return cursor.getLong(0)
                }
            }
        } catch (e: Exception) {
            Log.w("JARVIS", "VoIP query by name error: ${e.message}")
        }

        // 2. Direct match by phone digits in DATA1
        if (!cleanPhone.isNullOrBlank()) {
            try {
                val last7 = if (cleanPhone.length >= 7) cleanPhone.takeLast(7) else cleanPhone
                contentResolver.query(
                    ContactsContract.Data.CONTENT_URI,
                    arrayOf(ContactsContract.Data._ID),
                    "${ContactsContract.Data.MIMETYPE} = ? AND ${ContactsContract.Data.DATA1} LIKE ?",
                    arrayOf("vnd.android.cursor.item/vnd.com.whatsapp.voip.call", "%$last7%"),
                    null
                )?.use { cursor ->
                    if (cursor.moveToFirst()) {
                        return cursor.getLong(0)
                    }
                }
            } catch (e: Exception) {
                Log.w("JARVIS", "VoIP query by DATA1 error: ${e.message}")
            }
        }

        // 3. Resolve Contact ID first, then get WhatsApp VoIP row ID
        try {
            val filterUri = Uri.withAppendedPath(
                ContactsContract.CommonDataKinds.Phone.CONTENT_FILTER_URI,
                Uri.encode(trimmedTarget)
            )
            var contactId: Long? = null
            contentResolver.query(
                filterUri,
                arrayOf(ContactsContract.CommonDataKinds.Phone.CONTACT_ID),
                null, null, null
            )?.use { c ->
                if (c.moveToFirst()) {
                    contactId = c.getLong(0)
                }
            }

            if (contactId != null) {
                contentResolver.query(
                    ContactsContract.Data.CONTENT_URI,
                    arrayOf(ContactsContract.Data._ID),
                    "${ContactsContract.Data.CONTACT_ID} = ? AND ${ContactsContract.Data.MIMETYPE} = ?",
                    arrayOf(contactId.toString(), "vnd.android.cursor.item/vnd.com.whatsapp.voip.call"),
                    null
                )?.use { c ->
                    if (c.moveToFirst()) {
                        return c.getLong(0)
                    }
                }
            }
        } catch (e: Exception) {
            Log.w("JARVIS", "VoIP query by Contact ID error: ${e.message}")
        }

        return null
    }

    private fun findWhatsAppVideoCallDataId(target: String, cleanPhone: String?): Long? {
        if (checkSelfPermission(Manifest.permission.READ_CONTACTS) != PackageManager.PERMISSION_GRANTED) {
            return null
        }

        val trimmedTarget = target.trim()

        // 1. Direct match on WhatsApp Video Call MIME type by DISPLAY_NAME
        try {
            contentResolver.query(
                ContactsContract.Data.CONTENT_URI,
                arrayOf(ContactsContract.Data._ID),
                "${ContactsContract.Data.MIMETYPE} = ? AND ${ContactsContract.Data.DISPLAY_NAME} LIKE ?",
                arrayOf("vnd.android.cursor.item/vnd.com.whatsapp.video.call", "%$trimmedTarget%"),
                null
            )?.use { cursor ->
                if (cursor.moveToFirst()) {
                    return cursor.getLong(0)
                }
            }
        } catch (e: Exception) {
            Log.w("JARVIS", "VideoCall query by name error: ${e.message}")
        }

        // 2. Direct match by phone digits in DATA1
        if (!cleanPhone.isNullOrBlank()) {
            try {
                val last7 = if (cleanPhone.length >= 7) cleanPhone.takeLast(7) else cleanPhone
                contentResolver.query(
                    ContactsContract.Data.CONTENT_URI,
                    arrayOf(ContactsContract.Data._ID),
                    "${ContactsContract.Data.MIMETYPE} = ? AND ${ContactsContract.Data.DATA1} LIKE ?",
                    arrayOf("vnd.android.cursor.item/vnd.com.whatsapp.video.call", "%$last7%"),
                    null
                )?.use { cursor ->
                    if (cursor.moveToFirst()) {
                        return cursor.getLong(0)
                    }
                }
            } catch (e: Exception) {
                Log.w("JARVIS", "VideoCall query by DATA1 error: ${e.message}")
            }
        }

        // 3. Resolve Contact ID first, then get WhatsApp Video Call row ID
        try {
            val filterUri = Uri.withAppendedPath(
                ContactsContract.CommonDataKinds.Phone.CONTENT_FILTER_URI,
                Uri.encode(trimmedTarget)
            )
            var contactId: Long? = null
            contentResolver.query(
                filterUri,
                arrayOf(ContactsContract.CommonDataKinds.Phone.CONTACT_ID),
                null, null, null
            )?.use { c ->
                if (c.moveToFirst()) {
                    contactId = c.getLong(0)
                }
            }

            if (contactId != null) {
                contentResolver.query(
                    ContactsContract.Data.CONTENT_URI,
                    arrayOf(ContactsContract.Data._ID),
                    "${ContactsContract.Data.CONTACT_ID} = ? AND ${ContactsContract.Data.MIMETYPE} = ?",
                    arrayOf(contactId.toString(), "vnd.android.cursor.item/vnd.com.whatsapp.video.call"),
                    null
                )?.use { c ->
                    if (c.moveToFirst()) {
                        return c.getLong(0)
                    }
                }
            }
        } catch (e: Exception) {
            Log.w("JARVIS", "VideoCall query by Contact ID error: ${e.message}")
        }

        return null
    }

    private fun makeWhatsAppCall(target: String) {
        if (checkSelfPermission(Manifest.permission.READ_CONTACTS) != PackageManager.PERMISSION_GRANTED) {
            pendingWhatsAppCallTarget = target
            requestPermissions(arrayOf(Manifest.permission.READ_CONTACTS), CONTACTS_REQ_CODE)
            return
        }

        val phone = resolvePhoneNumber(target)
        val cleanPhone = if (!phone.isNullOrBlank()) formatWhatsAppPhone(phone) else null
        val voipDataId = findWhatsAppVoipDataId(target, cleanPhone)

        if (voipDataId != null) {
            try {
                val intent = Intent(Intent.ACTION_VIEW).apply {
                    setDataAndType(
                        Uri.parse("content://com.android.contacts/data/$voipDataId"),
                        "vnd.android.cursor.item/vnd.com.whatsapp.voip.call"
                    )
                    setPackage("com.whatsapp")
                    flags = Intent.FLAG_ACTIVITY_NEW_TASK
                }
                startActivity(intent)
                runOnUiThread {
                    Toast.makeText(this, "Iniciando llamada de WhatsApp a $target...", Toast.LENGTH_SHORT).show()
                }
                return
            } catch (e: Exception) {
                Log.e("JARVIS", "Error launching direct WhatsApp VoIP: ${e.message}")
            }
        }

        // Fallback A: Open direct chat with phone number
        if (!cleanPhone.isNullOrBlank() && cleanPhone.length >= 8) {
            try {
                val intent = Intent(Intent.ACTION_VIEW, Uri.parse("https://api.whatsapp.com/send?phone=$cleanPhone")).apply {
                    setPackage("com.whatsapp")
                    flags = Intent.FLAG_ACTIVITY_NEW_TASK
                }
                startActivity(intent)
                runOnUiThread {
                    Toast.makeText(this, "Abriendo WhatsApp con $target...", Toast.LENGTH_SHORT).show()
                }
                return
            } catch (e: Exception) {}
        }

        // Fallback B: If target has digits, dial direct phone call
        val directDigits = target.replace(Regex("[^0-9]"), "")
        if (directDigits.length >= 7) {
            dialDirect(directDigits)
        } else {
            runOnUiThread {
                Toast.makeText(this, "Contacto '$target' no encontrado en WhatsApp ni en la agenda telefónica", Toast.LENGTH_LONG).show()
            }
        }
    }

    private fun makeWhatsAppVideoCall(target: String) {
        if (checkSelfPermission(Manifest.permission.READ_CONTACTS) != PackageManager.PERMISSION_GRANTED) {
            pendingWhatsAppVideoCallTarget = target
            requestPermissions(arrayOf(Manifest.permission.READ_CONTACTS), CONTACTS_REQ_CODE)
            return
        }

        val phone = resolvePhoneNumber(target)
        val cleanPhone = if (!phone.isNullOrBlank()) formatWhatsAppPhone(phone) else null
        val videoDataId = findWhatsAppVideoCallDataId(target, cleanPhone)

        if (videoDataId != null) {
            try {
                val intent = Intent(Intent.ACTION_VIEW).apply {
                    setDataAndType(
                        Uri.parse("content://com.android.contacts/data/$videoDataId"),
                        "vnd.android.cursor.item/vnd.com.whatsapp.video.call"
                    )
                    setPackage("com.whatsapp")
                    flags = Intent.FLAG_ACTIVITY_NEW_TASK
                }
                startActivity(intent)
                runOnUiThread {
                    Toast.makeText(this, "Iniciando videollamada de WhatsApp con $target...", Toast.LENGTH_SHORT).show()
                }
                return
            } catch (e: Exception) {
                Log.e("JARVIS", "Error launching direct WhatsApp Video Call: ${e.message}")
            }
        }

        // Fallback: Open direct chat with phone number
        if (!cleanPhone.isNullOrBlank() && cleanPhone.length >= 8) {
            try {
                val intent = Intent(Intent.ACTION_VIEW, Uri.parse("https://api.whatsapp.com/send?phone=$cleanPhone")).apply {
                    setPackage("com.whatsapp")
                    flags = Intent.FLAG_ACTIVITY_NEW_TASK
                }
                startActivity(intent)
                runOnUiThread {
                    Toast.makeText(this, "Abriendo WhatsApp con $target...", Toast.LENGTH_SHORT).show()
                }
                return
            } catch (e: Exception) {}
        }

        runOnUiThread {
            Toast.makeText(this, "Contacto '$target' no encontrado para videollamada de WhatsApp", Toast.LENGTH_LONG).show()
        }
    }

    private fun sendWhatsApp(target: String, message: String) {
        if (checkSelfPermission(Manifest.permission.READ_CONTACTS) != PackageManager.PERMISSION_GRANTED) {
            pendingWhatsAppSendTarget = Pair(target, message)
            requestPermissions(arrayOf(Manifest.permission.READ_CONTACTS), CONTACTS_REQ_CODE)
            return
        }

        // Activate autonomous auto-send flag in AccessibilityService
        JarvisAccessibilityService.pendingAutoSend = true

        val phone = resolvePhoneNumber(target)
        val cleanPhone = if (!phone.isNullOrBlank()) formatWhatsAppPhone(phone) else null

        try {
            if (!cleanPhone.isNullOrBlank() && cleanPhone.length >= 8) {
                val url = "https://api.whatsapp.com/send?phone=$cleanPhone&text=${Uri.encode(message)}"
                val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url)).apply {
                    setPackage("com.whatsapp")
                    flags = Intent.FLAG_ACTIVITY_NEW_TASK
                }
                startActivity(intent)
                
                runOnUiThread {
                    if (isAccessibilityServiceEnabled()) {
                        Toast.makeText(this, "✓ J.A.R.V.I.S. transmitiendo y enviando a $target...", Toast.LENGTH_SHORT).show()
                    } else {
                        Toast.makeText(this, "Mensaje preparado. Para envío 100% automático sin tocar 'Enviar', active la Accesibilidad de J.A.R.V.I.S.", Toast.LENGTH_LONG).show()
                    }
                }
            } else {
                val url = "whatsapp://send?text=${Uri.encode(message)}"
                val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url)).apply {
                    setPackage("com.whatsapp")
                    flags = Intent.FLAG_ACTIVITY_NEW_TASK
                }
                startActivity(intent)
                runOnUiThread {
                    Toast.makeText(this, "Contacto '$target' no encontrado. Seleccione el contacto en WhatsApp:", Toast.LENGTH_LONG).show()
                }
            }
        } catch (e: Exception) {
            try {
                val fallbackIntent = Intent(Intent.ACTION_VIEW, Uri.parse("https://api.whatsapp.com/send?text=${Uri.encode(message)}")).apply {
                    flags = Intent.FLAG_ACTIVITY_NEW_TASK
                }
                startActivity(fallbackIntent)
            } catch (e2: Exception) {}
        }
    }

    private fun getGoogleCalendarId(): Long? {
        if (checkSelfPermission(Manifest.permission.READ_CALENDAR) != PackageManager.PERMISSION_GRANTED) {
            return null
        }

        val projection = arrayOf(
            CalendarContract.Calendars._ID,
            CalendarContract.Calendars.ACCOUNT_NAME,
            CalendarContract.Calendars.ACCOUNT_TYPE,
            CalendarContract.Calendars.IS_PRIMARY,
            CalendarContract.Calendars.CALENDAR_DISPLAY_NAME
        )

        // Strategy 1: Primary Google Calendar (account_type = com.google and is_primary = 1)
        try {
            contentResolver.query(
                CalendarContract.Calendars.CONTENT_URI,
                projection,
                "${CalendarContract.Calendars.ACCOUNT_TYPE} = ? AND ${CalendarContract.Calendars.IS_PRIMARY} = 1",
                arrayOf("com.google"),
                null
            )?.use { cursor ->
                if (cursor.moveToFirst()) {
                    val id = cursor.getLong(cursor.getColumnIndexOrThrow(CalendarContract.Calendars._ID))
                    Log.i("JARVIS", "Found primary Google Calendar ID: $id")
                    return id
                }
            }
        } catch (e: Exception) {
            Log.w("JARVIS", "Primary Google Calendar search failed: ${e.message}")
        }

        // Strategy 2: Any Google Calendar (account_type = com.google)
        try {
            contentResolver.query(
                CalendarContract.Calendars.CONTENT_URI,
                projection,
                "${CalendarContract.Calendars.ACCOUNT_TYPE} = ?",
                arrayOf("com.google"),
                "${CalendarContract.Calendars._ID} ASC"
            )?.use { cursor ->
                if (cursor.moveToFirst()) {
                    val id = cursor.getLong(cursor.getColumnIndexOrThrow(CalendarContract.Calendars._ID))
                    Log.i("JARVIS", "Found Google Calendar ID: $id")
                    return id
                }
            }
        } catch (e: Exception) {
            Log.w("JARVIS", "Any Google Calendar search failed: ${e.message}")
        }

        // Strategy 3: Any visible calendar
        try {
            contentResolver.query(
                CalendarContract.Calendars.CONTENT_URI,
                projection,
                "${CalendarContract.Calendars.VISIBLE} = 1",
                null,
                "${CalendarContract.Calendars._ID} ASC"
            )?.use { cursor ->
                if (cursor.moveToFirst()) {
                    val id = cursor.getLong(cursor.getColumnIndexOrThrow(CalendarContract.Calendars._ID))
                    Log.i("JARVIS", "Found fallback visible Calendar ID: $id")
                    return id
                }
            }
        } catch (e: Exception) {
            Log.w("JARVIS", "Visible Calendar search failed: ${e.message}")
        }

        return null
    }

    private fun triggerCalendarSync(calendarId: Long) {
        try {
            val cursor = contentResolver.query(
                CalendarContract.Calendars.CONTENT_URI,
                arrayOf(CalendarContract.Calendars.ACCOUNT_NAME, CalendarContract.Calendars.ACCOUNT_TYPE),
                "${CalendarContract.Calendars._ID} = ?",
                arrayOf(calendarId.toString()),
                null
            )
            cursor?.use {
                if (it.moveToFirst()) {
                    val accName = it.getString(0)
                    val accType = it.getString(1)
                    val account = android.accounts.Account(accName, accType)
                    val bundle = Bundle().apply {
                        putBoolean(ContentResolver.SYNC_EXTRAS_MANUAL, true)
                        putBoolean(ContentResolver.SYNC_EXTRAS_EXPEDITED, true)
                    }
                    ContentResolver.requestSync(account, CalendarContract.AUTHORITY, bundle)
                    Log.i("JARVIS", "Triggered calendar cloud sync for $accName ($accType)")
                }
            }
        } catch (e: Exception) {
            Log.w("JARVIS", "Trigger calendar sync error: ${e.message}")
        }
    }

    private fun addCalendarEvent(
        title: String,
        description: String?,
        startTimeMs: Long,
        endTimeMs: Long,
        location: String?
    ): Boolean {
        // 1. Ensure write calendar permission
        if (checkSelfPermission(Manifest.permission.WRITE_CALENDAR) != PackageManager.PERMISSION_GRANTED) {
            pendingCalendarEvent = CalendarEventData(title, description, startTimeMs, endTimeMs, location)
            requestPermissions(
                arrayOf(Manifest.permission.READ_CALENDAR, Manifest.permission.WRITE_CALENDAR),
                CALENDAR_REQ_CODE
            )
            return false
        }

        try {
            // 2. Locate user's Google Calendar ID
            val googleCalId = getGoogleCalendarId()
            if (googleCalId != null) {
                val values = ContentValues().apply {
                    put(CalendarContract.Events.CALENDAR_ID, googleCalId)
                    put(CalendarContract.Events.TITLE, title)
                    put(CalendarContract.Events.DESCRIPTION, description ?: "Agendado por J.A.R.V.I.S. Core")
                    put(CalendarContract.Events.DTSTART, startTimeMs)
                    put(CalendarContract.Events.DTEND, endTimeMs)
                    put(CalendarContract.Events.EVENT_TIMEZONE, TimeZone.getDefault().id)
                    if (!location.isNullOrBlank()) {
                        put(CalendarContract.Events.EVENT_LOCATION, location)
                    }
                    put(CalendarContract.Events.STATUS, CalendarContract.Events.STATUS_CONFIRMED)
                    put(CalendarContract.Events.HAS_ALARM, 1)
                }

                val eventUri = contentResolver.insert(CalendarContract.Events.CONTENT_URI, values)
                if (eventUri != null) {
                    // Add 15-minute reminder notification
                    val eventId = eventUri.lastPathSegment?.toLongOrNull()
                    if (eventId != null) {
                        try {
                            val reminderValues = ContentValues().apply {
                                put(CalendarContract.Reminders.EVENT_ID, eventId)
                                put(CalendarContract.Reminders.METHOD, CalendarContract.Reminders.METHOD_ALERT)
                                put(CalendarContract.Reminders.MINUTES, 15)
                            }
                            contentResolver.insert(CalendarContract.Reminders.CONTENT_URI, reminderValues)
                        } catch (e: Exception) {}
                    }

                    // Force immediate cloud sync to Google Calendar / Gmail
                    triggerCalendarSync(googleCalId)

                    runOnUiThread {
                        Toast.makeText(
                            this,
                            "✓ Evento agendado en Google Calendar: $title",
                            Toast.LENGTH_LONG
                        ).show()
                    }

                    // Open event view (viewing mode, already confirmed and saved)
                    try {
                        val viewIntent = Intent(Intent.ACTION_VIEW).apply {
                            data = eventUri
                            flags = Intent.FLAG_ACTIVITY_NEW_TASK
                        }
                        startActivity(viewIntent)
                    } catch (e: Exception) {
                        try {
                            val gcalIntent = packageManager.getLaunchIntentForPackage("com.google.android.calendar")
                            if (gcalIntent != null) {
                                gcalIntent.flags = Intent.FLAG_ACTIVITY_NEW_TASK
                                startActivity(gcalIntent)
                            }
                        } catch (e2: Exception) {}
                    }
                    return true
                }
            }
        } catch (e: Exception) {
            Log.e("JARVIS", "Error inserting calendar event directly: ${e.message}", e)
        }

        // Fallback: If direct insert failed, open intent
        try {
            val intent = Intent(Intent.ACTION_INSERT).apply {
                data = CalendarContract.Events.CONTENT_URI
                putExtra(CalendarContract.Events.TITLE, title)
                putExtra(CalendarContract.Events.DESCRIPTION, description ?: "")
                putExtra(CalendarContract.EXTRA_EVENT_BEGIN_TIME, startTimeMs)
                putExtra(CalendarContract.EXTRA_EVENT_END_TIME, endTimeMs)
                if (!location.isNullOrBlank()) {
                    putExtra(CalendarContract.Events.EVENT_LOCATION, location)
                }
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
            }
            startActivity(intent)
            return true
        } catch (e2: Exception) {
            return false
        }
    }
}
