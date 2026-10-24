package dev.voxhash.fsbcompanion.model

data class CompanionHealth(
    val status: String? = null,
    val service: String? = null,
    val version: String? = null,
    val auth_required: Boolean? = null,
    val read_only: Boolean? = null,
    val features: Map<String, Boolean>? = null,
)

data class PortfolioSnapshot(
    val balance: Double? = null,
    val equity: Double? = null,
    val status: String? = null,
    val positions_count: Int? = null,
    val trades_count: Int? = null,
    val last_update: String? = null,
    val read_only: Boolean? = null,
)

data class StrategiesResponse(
    val strategies: Map<String, StrategyHealth>? = null,
    val summary: StrategySummary? = null,
)

data class StrategySummary(
    val total: Int? = null,
    val by_status: Map<String, Int>? = null,
)

data class StrategyHealth(
    val strategy_name: String? = null,
    val status: String? = null,
    val signal_count: Int? = null,
    val error_count: Int? = null,
    val last_signal_time: String? = null,
)

data class PairingRedeemRequest(
    val pairing_code: String,
)

data class PairingRedeemResponse(
    val scheme: String? = null,
    val base_url: String? = null,
    val api_key: String? = null,
    val pin_sha256: String? = null,
    val redeemed_at: String? = null,
)

data class ActionRequest(
    val action: String,
    val requested_by: String = "android-companion",
)

data class ActionItem(
    val id: String? = null,
    val action: String? = null,
    val status: String? = null,
    val requested_by: String? = null,
    val created_at: String? = null,
)

data class ActionCreateResponse(
    val action: ActionItem? = null,
)

data class PendingActionsResponse(
    val pending: List<ActionItem>? = null,
    val count: Int? = null,
)

/** QR / paste payload from desktop pairing session. */
data class PairingQrPayload(
    val v: Int? = null,
    val scheme: String? = null,
    val base_url: String? = null,
    val pairing_code: String? = null,
    val expires_at: String? = null,
    val pin_sha256: String? = null,
)
