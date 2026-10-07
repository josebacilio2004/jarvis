package com.starkindustries.jarvis_flutter

import android.accessibilityservice.AccessibilityService
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import android.widget.Toast

class JarvisAccessibilityService : AccessibilityService() {

    companion object {
        @Volatile
        var pendingAutoSend: Boolean = false
        @Volatile
        var isServiceActive: Boolean = false
    }

    private val handler = Handler(Looper.getMainLooper())

    override fun onServiceConnected() {
        super.onServiceConnected()
        isServiceActive = true
        Log.i("JARVIS_ACCESSIBILITY", "J.A.R.V.I.S. Accessibility Service initialized and active")
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        if (!pendingAutoSend || event == null) return

        val pkg = event.packageName?.toString() ?: ""
        if (!pkg.contains("whatsapp")) return

        // Schedule button detection with a retry interval to allow WhatsApp text field to settle
        attemptAutoSend(0)
    }

    private fun attemptAutoSend(attempt: Int) {
        if (!pendingAutoSend || attempt > 5) return

        handler.postDelayed({
            if (!pendingAutoSend) return@postDelayed
            val root = rootInActiveWindow
            if (root != null && clickSendButton(root)) {
                pendingAutoSend = false
                Log.i("JARVIS_ACCESSIBILITY", "WhatsApp Send button clicked successfully on attempt $attempt")
                Toast.makeText(applicationContext, "✓ J.A.R.V.I.S.: Mensaje enviado con éxito", Toast.LENGTH_SHORT).show()
            } else {
                // Retry in 350ms
                attemptAutoSend(attempt + 1)
            }
        }, if (attempt == 0) 500L else 350L)
    }

    private fun clickSendButton(rootNode: AccessibilityNodeInfo): Boolean {
        // Strategy 1: Find by resource ID "com.whatsapp:id/send"
        try {
            val byId = rootNode.findAccessibilityNodeInfosByViewId("com.whatsapp:id/send")
            if (!byId.isNullOrEmpty()) {
                for (node in byId) {
                    if (node.isVisibleToUser) {
                        val clicked = node.performAction(AccessibilityNodeInfo.ACTION_CLICK)
                        if (clicked) return true
                    }
                }
            }
        } catch (e: Exception) {
            Log.w("JARVIS_ACCESSIBILITY", "ID lookup failed: ${e.message}")
        }

        // Strategy 2: Recursive search by ContentDescription or Text
        val matchingNodes = mutableListOf<AccessibilityNodeInfo>()
        collectSendCandidates(rootNode, matchingNodes)
        for (node in matchingNodes) {
            if (node.isVisibleToUser) {
                val clicked = node.performAction(AccessibilityNodeInfo.ACTION_CLICK)
                if (clicked) return true
            }
        }

        return false
    }

    private fun collectSendCandidates(node: AccessibilityNodeInfo?, list: MutableList<AccessibilityNodeInfo>) {
        if (node == null) return

        val desc = node.contentDescription?.toString()?.lowercase() ?: ""
        val text = node.text?.toString()?.lowercase() ?: ""
        val resName = node.viewIdResourceName?.lowercase() ?: ""

        if (desc.contains("enviar") || desc.contains("send") ||
            text.contains("enviar") || text.contains("send") ||
            resName.contains(":id/send")) {
            list.add(node)
        }

        for (i in 0 until node.childCount) {
            collectSendCandidates(node.getChild(i), list)
        }
    }

    override fun onInterrupt() {
        isServiceActive = false
        Log.i("JARVIS_ACCESSIBILITY", "J.A.R.V.I.S. Accessibility Service interrupted")
    }

    override fun onDestroy() {
        super.onDestroy()
        isServiceActive = false
    }
}
