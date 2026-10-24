package dev.voxhash.fsbcompanion.ui

import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import dev.voxhash.fsbcompanion.BuildConfig
import dev.voxhash.fsbcompanion.R
import dev.voxhash.fsbcompanion.api.CompanionClientFactory
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * Read-only companion: polls desktop RemoteMonitor companion endpoints.
 * No broker keys, no order placement, no Google Play Services.
 */
class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val baseUrl = findViewById<EditText>(R.id.inputBaseUrl)
        val apiKey = findViewById<EditText>(R.id.inputApiKey)
        val output = findViewById<TextView>(R.id.textOutput)
        val refresh = findViewById<Button>(R.id.btnRefresh)

        baseUrl.setText(BuildConfig.DEFAULT_BASE_URL)

        refresh.setOnClickListener {
            lifecycleScope.launch {
                output.text = "Loading…"
                val text = withContext(Dispatchers.IO) {
                    try {
                        val api = CompanionClientFactory.create(
                            baseUrl.text.toString().trim(),
                            apiKey.text.toString().trim(),
                        )
                        val health = api.health()
                        val bearer = "Bearer ${apiKey.text.toString().trim()}"
                        val portfolio = api.portfolio(bearer)
                        val strategies = api.strategies(bearer)
                        buildString {
                            appendLine("service=${health.service} v${health.version} read_only=${health.read_only}")
                            appendLine("equity=${portfolio.equity} balance=${portfolio.balance} status=${portfolio.status}")
                            appendLine("positions=${portfolio.positions_count} strategies=${strategies.summary?.total ?: 0}")
                            strategies.strategies?.forEach { (name, h) ->
                                appendLine(" - $name: ${h.status} signals=${h.signal_count} errors=${h.error_count}")
                            }
                        }
                    } catch (e: Exception) {
                        "Error: ${e.message}"
                    }
                }
                output.text = text
            }
        }
    }
}
