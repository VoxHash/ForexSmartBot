package dev.voxhash.fsbcompanion.ui

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

data class CompanionSession(
    val baseUrl: String,
    val apiKey: String,
    val pinSha256: String = "",
)

/**
 * Encrypted local cache for pairing session + last portfolio snapshot.
 * Uses EncryptedSharedPreferences (AES-256); falls back to private prefs if crypto init fails.
 */
object PairingPrefs {
    private const val PREFS = "fsb_companion_enc"
    private const val LEGACY_PREFS = "fsb_companion"
    private const val KEY_BASE = "base_url"
    private const val KEY_API = "api_key"
    private const val KEY_PIN = "pin_sha256"
    private const val KEY_CACHE_JSON = "portfolio_cache_json"
    private const val KEY_CACHE_AT = "portfolio_cache_at"

    private fun prefs(context: Context): SharedPreferences {
        return try {
            val master = MasterKey.Builder(context)
                .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
                .build()
            EncryptedSharedPreferences.create(
                context,
                PREFS,
                master,
                EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
                EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
            )
        } catch (_: Exception) {
            context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        }
    }

    fun load(context: Context): CompanionSession? {
        migrateLegacy(context)
        val p = prefs(context)
        val base = p.getString(KEY_BASE, null)?.trim().orEmpty()
        val key = p.getString(KEY_API, null)?.trim().orEmpty()
        if (base.isEmpty() || key.isEmpty()) return null
        return CompanionSession(base, key, p.getString(KEY_PIN, "")?.trim().orEmpty())
    }

    fun save(context: Context, session: CompanionSession) {
        prefs(context).edit()
            .putString(KEY_BASE, session.baseUrl.trim())
            .putString(KEY_API, session.apiKey.trim())
            .putString(KEY_PIN, session.pinSha256.trim())
            .apply()
    }

    fun clear(context: Context) {
        prefs(context).edit().clear().apply()
        context.getSharedPreferences(LEGACY_PREFS, Context.MODE_PRIVATE).edit().clear().apply()
    }

    fun savePortfolioCache(context: Context, json: String) {
        prefs(context).edit()
            .putString(KEY_CACHE_JSON, json)
            .putString(KEY_CACHE_AT, System.currentTimeMillis().toString())
            .apply()
    }

    fun loadPortfolioCache(context: Context): Pair<String, String>? {
        val p = prefs(context)
        val json = p.getString(KEY_CACHE_JSON, null)?.trim().orEmpty()
        val at = p.getString(KEY_CACHE_AT, null)?.trim().orEmpty()
        if (json.isEmpty()) return null
        return json to at
    }

    private fun migrateLegacy(context: Context) {
        val legacy = context.getSharedPreferences(LEGACY_PREFS, Context.MODE_PRIVATE)
        val base = legacy.getString(KEY_BASE, null)?.trim().orEmpty()
        val key = legacy.getString(KEY_API, null)?.trim().orEmpty()
        if (base.isEmpty() || key.isEmpty()) return
        val enc = prefs(context)
        if (enc.getString(KEY_BASE, null).isNullOrBlank()) {
            enc.edit()
                .putString(KEY_BASE, base)
                .putString(KEY_API, key)
                .putString(KEY_PIN, legacy.getString(KEY_PIN, "")?.trim().orEmpty())
                .apply()
        }
        legacy.edit().clear().apply()
    }
}
