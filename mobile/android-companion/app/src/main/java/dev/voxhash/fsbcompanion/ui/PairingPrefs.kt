package dev.voxhash.fsbcompanion.ui

import android.content.Context

data class CompanionSession(
    val baseUrl: String,
    val apiKey: String,
    val pinSha256: String = "",
)

object PairingPrefs {
    private const val PREFS = "fsb_companion"
    private const val KEY_BASE = "base_url"
    private const val KEY_API = "api_key"
    private const val KEY_PIN = "pin_sha256"

    fun load(context: Context): CompanionSession? {
        val p = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val base = p.getString(KEY_BASE, null)?.trim().orEmpty()
        val key = p.getString(KEY_API, null)?.trim().orEmpty()
        if (base.isEmpty() || key.isEmpty()) return null
        return CompanionSession(base, key, p.getString(KEY_PIN, "")?.trim().orEmpty())
    }

    fun save(context: Context, session: CompanionSession) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
            .putString(KEY_BASE, session.baseUrl.trim())
            .putString(KEY_API, session.apiKey.trim())
            .putString(KEY_PIN, session.pinSha256.trim())
            .apply()
    }

    fun clear(context: Context) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().clear().apply()
    }
}
