package de.phonedeck

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

/** Nach dem Hochfahren: Waechter-Dienst und Deck automatisch starten. */
class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        PowerWatchService.start(context)
        try {
            context.startActivity(
                Intent(context, MainActivity::class.java)
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            )
        } catch (_: Exception) {
            // Ohne Overlay-Recht ggf. blockiert; als Startbildschirm oeffnet es trotzdem.
        }
    }
}
