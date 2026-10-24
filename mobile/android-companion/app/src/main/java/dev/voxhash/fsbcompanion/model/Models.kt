package dev.voxhash.fsbcompanion.model

data class CompanionHealth(
    val status: String? = null,
    val service: String? = null,
    val version: String? = null,
    val auth_required: Boolean? = null,
    val read_only: Boolean? = null,
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
