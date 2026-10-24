package dev.voxhash.fsbcompanion.ui

import android.graphics.ImageDecoder
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.MediaStore
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import dev.voxhash.fsbcompanion.BuildConfig
import dev.voxhash.fsbcompanion.api.CompanionClientFactory
import dev.voxhash.fsbcompanion.model.ActionRequest
import dev.voxhash.fsbcompanion.model.PairingRedeemRequest
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * Compose companion: QR/paste pairing, portfolio + strategies, request stop/start
 * (host must approve). No broker keys, no Google Play Services.
 */
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme(colorScheme = darkColorScheme()) {
                Surface(modifier = Modifier.fillMaxSize()) {
                    CompanionApp()
                }
            }
        }
    }
}

@Composable
private fun CompanionApp() {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var session by remember { mutableStateOf(PairingPrefs.load(context)) }
    var baseUrl by remember {
        mutableStateOf(session?.baseUrl ?: BuildConfig.DEFAULT_BASE_URL)
    }
    var apiKey by remember { mutableStateOf(session?.apiKey ?: "") }
    var pin by remember { mutableStateOf(session?.pinSha256 ?: "") }
    var pairingPaste by remember { mutableStateOf("") }
    var output by remember { mutableStateOf("Paste pairing JSON or pick a QR image from the desktop dashboard.") }
    var busy by remember { mutableStateOf(false) }

    val pickQr = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri: Uri? ->
        if (uri == null) return@rememberLauncherForActivityResult
        scope.launch {
            busy = true
            val text = withContext(Dispatchers.IO) {
                try {
                    val bitmap = if (Build.VERSION.SDK_INT >= 28) {
                        ImageDecoder.decodeBitmap(ImageDecoder.createSource(context.contentResolver, uri))
                    } else {
                        @Suppress("DEPRECATION")
                        MediaStore.Images.Media.getBitmap(context.contentResolver, uri)
                    }
                    PairingParser.decodeBitmap(bitmap)
                } catch (e: Exception) {
                    null
                }
            }
            if (text == null) {
                output = "Could not decode QR from image"
            } else {
                pairingPaste = text
                output = "QR decoded — tap Redeem pairing"
            }
            busy = false
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("FSB Companion", style = MaterialTheme.typography.headlineSmall)
        Text(
            "GrapheneOS-friendly · read monitoring · host approve/reject for control",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )

        Text("Pairing", style = MaterialTheme.typography.titleMedium)
        OutlinedTextField(
            value = pairingPaste,
            onValueChange = { pairingPaste = it },
            label = { Text("Paste QR JSON from desktop") },
            modifier = Modifier.fillMaxWidth(),
            minLines = 3,
        )
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedButton(onClick = { pickQr.launch("image/*") }, enabled = !busy) {
                Text("Scan QR image")
            }
            Button(
                enabled = !busy && pairingPaste.isNotBlank(),
                onClick = {
                    scope.launch {
                        busy = true
                        output = redeemPairing(context, pairingPaste)?.also { s ->
                            session = s
                            baseUrl = s.baseUrl
                            apiKey = s.apiKey
                            pin = s.pinSha256
                        }?.let { "Paired with ${it.baseUrl}" }
                            ?: "Pairing failed — check code / expiry"
                        busy = false
                    }
                },
            ) { Text("Redeem pairing") }
        }

        Text("Connection", style = MaterialTheme.typography.titleMedium)
        OutlinedTextField(
            value = baseUrl,
            onValueChange = { baseUrl = it },
            label = { Text("Base URL") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
        )
        OutlinedTextField(
            value = apiKey,
            onValueChange = { apiKey = it },
            label = { Text("API key") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
        )
        OutlinedTextField(
            value = pin,
            onValueChange = { pin = it },
            label = { Text("Cert pin sha256/… (optional)") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
        )

        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(
                enabled = !busy,
                onClick = {
                    scope.launch {
                        busy = true
                        val s = CompanionSession(baseUrl.trim(), apiKey.trim(), pin.trim())
                        PairingPrefs.save(context, s)
                        session = s
                        output = refreshSnapshot(s)
                        busy = false
                    }
                },
            ) { Text("Refresh") }
            OutlinedButton(
                enabled = !busy && session != null,
                onClick = {
                    PairingPrefs.clear(context)
                    session = null
                    apiKey = ""
                    pin = ""
                    output = "Session cleared"
                },
            ) { Text("Unpair") }
        }

        Text("Request host action", style = MaterialTheme.typography.titleMedium)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedButton(
                enabled = !busy && apiKey.isNotBlank(),
                onClick = {
                    scope.launch {
                        busy = true
                        output = requestAction(baseUrl, apiKey, pin, "stop_trading")
                        busy = false
                    }
                },
            ) { Text("Request stop") }
            OutlinedButton(
                enabled = !busy && apiKey.isNotBlank(),
                onClick = {
                    scope.launch {
                        busy = true
                        output = requestAction(baseUrl, apiKey, pin, "start_trading")
                        busy = false
                    }
                },
            ) { Text("Request start") }
        }

        Text(output, style = MaterialTheme.typography.bodyMedium)
    }
}

private suspend fun redeemPairing(context: android.content.Context, raw: String): CompanionSession? {
    return withContext(Dispatchers.IO) {
        val payload = PairingParser.parseQrText(raw) ?: return@withContext null
        val base = payload.base_url?.trim().orEmpty()
        val code = payload.pairing_code?.trim().orEmpty()
        if (base.isEmpty() || code.isEmpty()) return@withContext null
        try {
            val api = CompanionClientFactory.create(base, "", payload.pin_sha256.orEmpty())
            val redeemed = api.redeemPairing(PairingRedeemRequest(code))
            val key = redeemed.api_key?.trim().orEmpty()
            val url = redeemed.base_url?.trim().orEmpty().ifEmpty { base }
            if (key.isEmpty()) return@withContext null
            val session = CompanionSession(url, key, redeemed.pin_sha256.orEmpty())
            PairingPrefs.save(context, session)
            session
        } catch (_: Exception) {
            null
        }
    }
}

private suspend fun refreshSnapshot(session: CompanionSession): String {
    return withContext(Dispatchers.IO) {
        try {
            val api = CompanionClientFactory.create(session.baseUrl, session.apiKey, session.pinSha256)
            val health = api.health()
            val portfolio = api.portfolio()
            val strategies = api.strategies()
            val pending = try {
                api.pendingActions()
            } catch (_: Exception) {
                null
            }
            buildString {
                appendLine("service=${health.service} v${health.version} read_only=${health.read_only}")
                appendLine("equity=${portfolio.equity} balance=${portfolio.balance} status=${portfolio.status}")
                appendLine("positions=${portfolio.positions_count} strategies=${strategies.summary?.total ?: 0}")
                strategies.strategies?.forEach { (name, h) ->
                    appendLine(" - $name: ${h.status} signals=${h.signal_count} errors=${h.error_count}")
                }
                if (pending != null) {
                    appendLine("pending_actions=${pending.count ?: pending.pending?.size ?: 0}")
                }
            }
        } catch (e: Exception) {
            "Error: ${e.message}"
        }
    }
}

private suspend fun requestAction(
    baseUrl: String,
    apiKey: String,
    pin: String,
    action: String,
): String {
    return withContext(Dispatchers.IO) {
        try {
            val api = CompanionClientFactory.create(baseUrl.trim(), apiKey.trim(), pin.trim())
            val resp = api.requestAction(ActionRequest(action = action))
            val item = resp.action
            "Requested ${item?.action} id=${item?.id} status=${item?.status} — approve on desktop dashboard"
        } catch (e: Exception) {
            "Action failed: ${e.message}"
        }
    }
}
