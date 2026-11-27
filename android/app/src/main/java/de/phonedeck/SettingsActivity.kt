package de.phonedeck

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.PowerManager
import android.provider.Settings
import android.text.InputType
import android.widget.Button
import android.widget.CheckBox
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast

class SettingsActivity : Activity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (Build.VERSION.SDK_INT >= 33) {
            requestPermissions(arrayOf(android.Manifest.permission.POST_NOTIFICATIONS), 1)
        }

        val col = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(48, 48, 48, 48)
        }
        fun label(t: String) = col.addView(TextView(this).apply { text = t; setPadding(0, 24, 0, 4) })

        label("PC-Adresse (IP, z.B. 192.168.1.20 – steht im Server-Fenster)")
        val host = EditText(this).apply { setText(Prefs.host(this@SettingsActivity)); hint = "192.168.1.20" }
        col.addView(host)

        label("Port")
        val port = EditText(this).apply {
            inputType = InputType.TYPE_CLASS_NUMBER
            setText(Prefs.port(this@SettingsActivity).toString())
        }
        col.addView(port)

        val shutdown = CheckBox(this).apply {
            text = "Komplett ausschalten statt Standby (braucht Root)"
            isChecked = Prefs.shutdownEnabled(this@SettingsActivity)
        }
        col.addView(shutdown)

        label("Wartezeit vor dem Ausschalten (Sekunden)")
        val delay = EditText(this).apply {
            inputType = InputType.TYPE_CLASS_NUMBER
            setText(Prefs.shutdownDelaySec(this@SettingsActivity).toString())
        }
        col.addView(delay)

        fun button(t: String, action: () -> Unit) =
            col.addView(Button(this).apply { text = t; setOnClickListener { action() } })

        button("Speichern") {
            Prefs.save(
                this, host.text.toString(),
                port.text.toString().toIntOrNull() ?: 8765,
                shutdown.isChecked,
                delay.text.toString().toIntOrNull() ?: 15
            )
            toast("Gespeichert")
            finish()
        }

        label("Einrichtung (einmalig):")
        button("0. Standby erlauben (Bildschirm sofort aus, ohne Root)") {
            if (AdminReceiver.isActive(this)) toast("Schon erledigt ✅")
            else startActivity(
                Intent(android.app.admin.DevicePolicyManager.ACTION_ADD_DEVICE_ADMIN)
                    .putExtra(android.app.admin.DevicePolicyManager.EXTRA_DEVICE_ADMIN, AdminReceiver.component(this))
                    .putExtra(android.app.admin.DevicePolicyManager.EXTRA_ADD_EXPLANATION,
                        "Damit PhoneDeck den Bildschirm ausschalten kann, wenn der PC aus ist.")
            )
        }
        button("1. Root testen") {
            Thread {
                val ok = Root.available()
                runOnUiThread { toast(if (ok) "Root OK ✅" else "Kein Root ❌ – Ausschalten geht nicht") }
            }.start()
        }
        button("2. Über anderen Apps einblenden erlauben") {
            startActivity(
                Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:$packageName"))
            )
        }
        button("3. Akku-Optimierung abschalten") {
            val pm = getSystemService(PowerManager::class.java)
            if (pm.isIgnoringBatteryOptimizations(packageName)) toast("Schon erledigt ✅")
            else startActivity(
                Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, Uri.parse("package:$packageName"))
            )
        }
        button("4. PhoneDeck als Startbildschirm wählen") {
            startActivity(Intent(Settings.ACTION_HOME_SETTINGS))
        }
        button("Deck verlassen (normalen Launcher öffnen)") {
            startActivity(Intent(Settings.ACTION_SETTINGS))
        }

        setContentView(ScrollView(this).apply { addView(col) })
    }

    private fun toast(t: String) = Toast.makeText(this, t, Toast.LENGTH_LONG).show()
}
