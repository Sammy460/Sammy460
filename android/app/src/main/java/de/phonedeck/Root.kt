package de.phonedeck

import java.util.concurrent.TimeUnit

/** Root-Befehle ueber "su" (Magisk, KernelSU, ...). */
object Root {
    private fun su(cmd: String, timeoutSec: Long = 10): String? = try {
        val p = ProcessBuilder("su", "-c", cmd).redirectErrorStream(true).start()
        val out = p.inputStream.bufferedReader().readText()
        if (!p.waitFor(timeoutSec, TimeUnit.SECONDS)) p.destroy()
        if (p.exitValue() == 0) out else null
    } catch (e: Exception) {
        null
    }

    /** Fragt Root an (Magisk zeigt beim ersten Mal einen Dialog). */
    fun available(): Boolean = su("id")?.contains("uid=0") == true

    /** Schaltet das Handy komplett aus. */
    fun shutdown(): Boolean =
        su("reboot -p") != null || su("svc power shutdown") != null
}
