package de.phonedeck

import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.BatteryManager

object Prefs {
    private fun sp(ctx: Context) = ctx.getSharedPreferences("phonedeck", Context.MODE_PRIVATE)

    fun host(ctx: Context): String = sp(ctx).getString("host", "") ?: ""
    fun port(ctx: Context): Int = sp(ctx).getInt("port", 8765)
    fun shutdownEnabled(ctx: Context): Boolean = sp(ctx).getBoolean("shutdown", false)
    fun shutdownDelaySec(ctx: Context): Int = sp(ctx).getInt("delay", 15)

    fun url(ctx: Context) = "http://${host(ctx)}:${port(ctx)}/"

    fun save(ctx: Context, host: String, port: Int, shutdown: Boolean, delay: Int) {
        sp(ctx).edit()
            .putString("host", host.trim())
            .putInt("port", port)
            .putBoolean("shutdown", shutdown)
            .putInt("delay", delay.coerceAtLeast(3))
            .apply()
    }

    fun isPluggedIn(ctx: Context): Boolean {
        val status = ctx.registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
        return (status?.getIntExtra(BatteryManager.EXTRA_PLUGGED, 0) ?: 0) != 0
    }
}
