package de.phonedeck

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.os.PowerManager

/**
 * Laeuft dauerhaft im Hintergrund.
 * - USB-Strom weg (PC aus)  -> nach Wartezeit Handy ausschalten (Root)
 * - USB-Strom wieder da     -> Ausschalten abbrechen, Bildschirm an, Deck oeffnen
 */
class PowerWatchService : Service() {

    private val handler = Handler(Looper.getMainLooper())

    private val shutdownTask = Runnable {
        if (!Prefs.isPluggedIn(this) && Prefs.shutdownEnabled(this)) {
            notify("Schalte aus …")
            if (!Root.shutdown()) {
                notify("Kein Root – Standby statt Ausschalten")
                AdminReceiver.screenOff(this)
            }
        }
    }

    private val receiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            when (intent.action) {
                Intent.ACTION_POWER_DISCONNECTED -> onUnplugged()
                Intent.ACTION_POWER_CONNECTED -> onPluggedIn()
            }
        }
    }

    private fun onUnplugged() {
        handler.removeCallbacks(shutdownTask)
        if (Prefs.shutdownEnabled(this)) {
            val sec = Prefs.shutdownDelaySec(this)
            notify("PC getrennt – schalte in $sec s aus")
            handler.postDelayed(shutdownTask, sec * 1000L)
        } else {
            // Standby-Modus (ohne Root): Bildschirm sofort aus
            notify("PC getrennt – Standby")
            AdminReceiver.screenOff(this)
        }
    }

    private fun onPluggedIn() {
        handler.removeCallbacks(shutdownTask)
        notify("Mit PC verbunden")
        wakeScreen()
        try {
            startActivity(
                Intent(this, MainActivity::class.java)
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_REORDER_TO_FRONT)
            )
        } catch (_: Exception) {
        }
    }

    @Suppress("DEPRECATION")
    private fun wakeScreen() {
        val pm = getSystemService(Context.POWER_SERVICE) as PowerManager
        val wl = pm.newWakeLock(
            PowerManager.SCREEN_BRIGHT_WAKE_LOCK or PowerManager.ACQUIRE_CAUSES_WAKEUP,
            "phonedeck:wake"
        )
        wl.acquire(3000)
    }

    override fun onCreate() {
        super.onCreate()
        val nm = getSystemService(NotificationManager::class.java)
        if (Build.VERSION.SDK_INT >= 26) {
            nm.createNotificationChannel(
                NotificationChannel(CHANNEL, "PhoneDeck", NotificationManager.IMPORTANCE_LOW)
            )
        }
        val n = build(if (Prefs.isPluggedIn(this)) "Mit PC verbunden" else "PC getrennt")
        if (Build.VERSION.SDK_INT >= 34) {
            startForeground(NOTIF_ID, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE)
        } else {
            startForeground(NOTIF_ID, n)
        }
        registerReceiver(receiver, IntentFilter().apply {
            addAction(Intent.ACTION_POWER_CONNECTED)
            addAction(Intent.ACTION_POWER_DISCONNECTED)
        })
        // Bewusst KEIN Ausschalten, wenn ohne Strom gestartet:
        // so kann man das Handy jederzeit von Hand einschalten und einstellen.
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int) = START_STICKY

    override fun onDestroy() {
        handler.removeCallbacks(shutdownTask)
        unregisterReceiver(receiver)
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    @Suppress("DEPRECATION")
    private fun build(text: String): Notification {
        val b = if (Build.VERSION.SDK_INT >= 26) Notification.Builder(this, CHANNEL)
        else Notification.Builder(this)
        return b.setContentTitle("PhoneDeck")
            .setContentText(text)
            .setSmallIcon(android.R.drawable.ic_lock_power_off)
            .setOngoing(true)
            .build()
    }

    private fun notify(text: String) {
        getSystemService(NotificationManager::class.java).notify(NOTIF_ID, build(text))
    }

    companion object {
        private const val CHANNEL = "phonedeck"
        private const val NOTIF_ID = 1

        fun start(ctx: Context) {
            val i = Intent(ctx, PowerWatchService::class.java)
            if (Build.VERSION.SDK_INT >= 26) ctx.startForegroundService(i) else ctx.startService(i)
        }
    }
}
