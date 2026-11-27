package de.phonedeck

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import android.os.PowerManager
import java.net.HttpURLConnection
import java.net.URL
import kotlin.concurrent.thread

/**
 * Laeuft dauerhaft im Hintergrund und fragt den PC-Server regelmaessig ab.
 * - Server erreichbar (PC an)   -> Bildschirm an, Deck nach vorne.
 * - Server weg (PC aus)         -> nach Wartezeit Bildschirm aus (Standby),
 *                                  mit Root stattdessen ganz ausschalten.
 * Funktioniert ueber WLAN und ueber Kabel (adb reverse auf 127.0.0.1).
 */
class PowerWatchService : Service() {

    @Volatile private var running = true
    @Volatile private var online = true
    private var offSince = 0L

    private fun pingOk(): Boolean = try {
        val c = URL(Prefs.url(this) + "api/ping").openConnection() as HttpURLConnection
        c.connectTimeout = 1500
        c.readTimeout = 1500
        c.requestMethod = "GET"
        val ok = c.responseCode == 200
        c.disconnect()
        ok
    } catch (_: Exception) {
        false
    }

    private fun loop() {
        while (running) {
            if (Prefs.host(this).isEmpty()) {
                Thread.sleep(2000); continue
            }
            val ok = pingOk()
            when {
                ok && !online -> onBackOnline()
                !ok && online -> {
                    if (offSince == 0L) offSince = System.currentTimeMillis()
                    val delayMs = Prefs.shutdownDelaySec(this) * 1000L
                    if (System.currentTimeMillis() - offSince >= delayMs) onGoneOffline()
                }
            }
            Thread.sleep(2000)
        }
    }

    private fun onGoneOffline() {
        online = false
        offSince = 0L
        if (Prefs.shutdownEnabled(this) && Root.shutdown()) {
            notify("PC aus – Handy wird ausgeschaltet")
            return
        }
        notify("PC aus – Standby")
        AdminReceiver.screenOff(this)
    }

    private fun onBackOnline() {
        online = true
        offSince = 0L
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
        val n = build("PhoneDeck laeuft")
        if (Build.VERSION.SDK_INT >= 34) {
            startForeground(NOTIF_ID, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE)
        } else {
            startForeground(NOTIF_ID, n)
        }
        thread(isDaemon = true) { loop() }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int) = START_STICKY

    override fun onDestroy() {
        running = false
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
