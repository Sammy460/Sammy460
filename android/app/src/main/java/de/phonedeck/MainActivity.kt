package de.phonedeck

import android.app.Activity
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.graphics.Color
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.Gravity
import android.view.View
import android.view.WindowManager
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.FrameLayout
import android.widget.TextView
import android.widget.Toast

/** Vollbild-Deck: zeigt die Button-Seite vom PC an. */
class MainActivity : Activity() {

    private lateinit var web: WebView
    private val handler = Handler(Looper.getMainLooper())
    private val retry = Runnable { loadDeck() }

    private val powerReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) = updateKeepScreenOn()
    }

    @Suppress("DEPRECATION")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (Build.VERSION.SDK_INT >= 27) {
            setShowWhenLocked(true)
            setTurnScreenOn(true)
        } else {
            window.addFlags(
                WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED or
                    WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON
            )
        }

        web = WebView(this).apply {
            setBackgroundColor(Color.parseColor("#0d0d0f"))
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            settings.cacheMode = WebSettings.LOAD_NO_CACHE
            webViewClient = object : WebViewClient() {
                override fun onReceivedError(
                    view: WebView, request: WebResourceRequest, error: WebResourceError
                ) {
                    if (request.isForMainFrame) showWaiting()
                }
            }
        }

        // Kleines Zahnrad oben rechts: LANGE druecken -> Einstellungen
        val gear = TextView(this).apply {
            text = "⚙"
            textSize = 22f
            setTextColor(Color.WHITE)
            alpha = 0.25f
            setPadding(24, 8, 24, 8)
            setOnClickListener {
                Toast.makeText(this@MainActivity, "Lange drücken für Einstellungen", Toast.LENGTH_SHORT).show()
            }
            setOnLongClickListener {
                startActivity(Intent(this@MainActivity, SettingsActivity::class.java)); true
            }
        }

        setContentView(FrameLayout(this).apply {
            addView(web)
            addView(gear, FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.WRAP_CONTENT, FrameLayout.LayoutParams.WRAP_CONTENT,
                Gravity.TOP or Gravity.END
            ))
        })

        PowerWatchService.start(this)
        if (Prefs.host(this).isEmpty()) {
            startActivity(Intent(this, SettingsActivity::class.java))
        }
    }

    override fun onResume() {
        super.onResume()
        hideSystemUi()
        registerReceiver(powerReceiver, IntentFilter().apply {
            addAction(Intent.ACTION_POWER_CONNECTED)
            addAction(Intent.ACTION_POWER_DISCONNECTED)
        })
        updateKeepScreenOn()
        loadDeck()
    }

    override fun onPause() {
        handler.removeCallbacks(retry)
        unregisterReceiver(powerReceiver)
        super.onPause()
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        // Kiosk: Zurueck-Taste ignorieren
    }

    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (hasFocus) hideSystemUi()
    }

    private fun loadDeck() {
        handler.removeCallbacks(retry)
        if (Prefs.host(this).isEmpty()) {
            showWaiting("Keine PC-Adresse eingestellt (⚙ lange drücken)")
            return
        }
        web.loadUrl(Prefs.url(this))
    }

    private fun showWaiting(msg: String = "Warte auf PC …") {
        val html = """
            <html><body style="margin:0;height:100%;background:#0d0d0f;color:#888;
              font-family:sans-serif;display:flex;align-items:center;justify-content:center">
              <div>$msg</div></body></html>
        """.trimIndent()
        web.loadDataWithBaseURL(null, html, "text/html", "utf-8", null)
        handler.removeCallbacks(retry)
        handler.postDelayed(retry, 3000)
    }

    /** Am PC-Strom: Bildschirm bleibt an. Ohne Strom: normal ausgehen lassen. */
    private fun updateKeepScreenOn() {
        if (Prefs.isPluggedIn(this)) {
            window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        } else {
            window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        }
    }

    @Suppress("DEPRECATION")
    private fun hideSystemUi() {
        window.decorView.systemUiVisibility = (View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
            or View.SYSTEM_UI_FLAG_FULLSCREEN
            or View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
            or View.SYSTEM_UI_FLAG_LAYOUT_STABLE
            or View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
            or View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN)
    }
}
