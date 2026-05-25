package com.digifake.overlayhud

import android.annotation.SuppressLint
import android.app.Service
import android.content.Intent
import android.graphics.PixelFormat
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.telephony.TelephonyCallback
import android.telephony.TelephonyManager
import android.view.LayoutInflater
import android.view.WindowManager
import android.view.View
import android.widget.TextView

class OverlayService : Service() {

    private lateinit var windowManager: WindowManager
    private var overlayView: View? = null
    private lateinit var telephonyManager: TelephonyManager
    private lateinit var telephonyCallback: TelephonyCallback

    private var secondsElapsed = 0
    private val handler = Handler(Looper.getMainLooper())
    private val timerRunnable = object : Runnable {
        override fun run() {
            secondsElapsed++
            val minutes = secondsElapsed / 60
            val seconds = secondsElapsed % 60
            val timeString = String.format("%02d:%02d", minutes, seconds)
            overlayView?.findViewById<TextView>(R.id.tvTimer)?.text = timeString
            handler.postDelayed(this, 1000)
        }
    }

    override fun onBind(intent: Intent?): IBinder? = null

    @SuppressLint("MissingPermission")
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        windowManager = getSystemService(WINDOW_SERVICE) as WindowManager
        telephonyManager = getSystemService(TELEPHONY_SERVICE) as TelephonyManager

        telephonyCallback = object : TelephonyCallback(), TelephonyCallback.CallStateListener {
            override fun onCallStateChanged(state: Int) {
                when (state) {
                    TelephonyManager.CALL_STATE_OFFHOOK -> showOverlay()
                    TelephonyManager.CALL_STATE_IDLE -> hideOverlay()
                }
            }
        }

        telephonyManager.registerTelephonyCallback(mainExecutor, telephonyCallback)
        return START_STICKY
    }

    private fun showOverlay() {
        if (overlayView != null) return

        overlayView = LayoutInflater.from(this).inflate(R.layout.overlay_layout, null)

        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
            PixelFormat.TRANSLUCENT
        )

        windowManager.addView(overlayView, params)
        secondsElapsed = 0
        handler.post(timerRunnable)
    }

    private fun hideOverlay() {
        handler.removeCallbacks(timerRunnable)
        overlayView?.let {
            windowManager.removeView(it)
            overlayView = null
        }
    }

    override fun onDestroy() {
        handler.removeCallbacks(timerRunnable)
        telephonyManager.unregisterTelephonyCallback(telephonyCallback)
        hideOverlay()
        super.onDestroy()
    }
}