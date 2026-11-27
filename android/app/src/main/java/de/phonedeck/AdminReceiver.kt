package de.phonedeck

import android.app.admin.DeviceAdminReceiver
import android.app.admin.DevicePolicyManager
import android.content.ComponentName
import android.content.Context

/** Erlaubt das sofortige Ausschalten des Bildschirms (ohne Root). */
class AdminReceiver : DeviceAdminReceiver() {
    companion object {
        fun component(ctx: Context) = ComponentName(ctx, AdminReceiver::class.java)

        fun isActive(ctx: Context) =
            ctx.getSystemService(DevicePolicyManager::class.java).isAdminActive(component(ctx))

        /** Bildschirm sofort aus. */
        fun screenOff(ctx: Context): Boolean {
            if (!isActive(ctx)) return false
            ctx.getSystemService(DevicePolicyManager::class.java).lockNow()
            return true
        }
    }
}
