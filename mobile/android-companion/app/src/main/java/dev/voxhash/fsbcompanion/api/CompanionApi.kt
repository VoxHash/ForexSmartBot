package dev.voxhash.fsbcompanion.api

import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import dev.voxhash.fsbcompanion.BuildConfig
import dev.voxhash.fsbcompanion.model.ActionCreateResponse
import dev.voxhash.fsbcompanion.model.ActionRequest
import dev.voxhash.fsbcompanion.model.CompanionHealth
import dev.voxhash.fsbcompanion.model.PairingRedeemRequest
import dev.voxhash.fsbcompanion.model.PairingRedeemResponse
import dev.voxhash.fsbcompanion.model.PendingActionsResponse
import dev.voxhash.fsbcompanion.model.PortfolioSnapshot
import dev.voxhash.fsbcompanion.model.StrategiesResponse
import okhttp3.CertificatePinner
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import java.util.concurrent.TimeUnit

interface CompanionService {
    @GET("api/v1/companion/health")
    suspend fun health(): CompanionHealth

    @GET("api/v1/companion/portfolio")
    suspend fun portfolio(): PortfolioSnapshot

    @GET("api/v1/companion/strategies")
    suspend fun strategies(): StrategiesResponse

    @POST("api/v1/companion/pairing/redeem")
    suspend fun redeemPairing(@Body body: PairingRedeemRequest): PairingRedeemResponse

    @POST("api/v1/companion/actions")
    suspend fun requestAction(@Body body: ActionRequest): ActionCreateResponse

    @GET("api/v1/companion/actions")
    suspend fun pendingActions(): PendingActionsResponse
}

object CompanionClientFactory {
    private val moshi: Moshi = Moshi.Builder()
        .add(KotlinJsonAdapterFactory())
        .build()

    fun create(baseUrl: String, apiKey: String, pinSha256: String = ""): CompanionService {
        val auth = Interceptor { chain ->
            val req = chain.request().newBuilder()
            if (apiKey.isNotBlank()) {
                req.header("Authorization", "Bearer $apiKey")
                req.header("X-API-Key", apiKey)
            }
            chain.proceed(req.build())
        }
        val builder = OkHttpClient.Builder()
            .connectTimeout(10, TimeUnit.SECONDS)
            .readTimeout(15, TimeUnit.SECONDS)
            .addInterceptor(auth)

        val pinner = buildCertificatePinner(baseUrl, pinSha256)
        if (pinner != null) {
            builder.certificatePinner(pinner)
        }

        val root = if (baseUrl.endsWith("/")) baseUrl else "$baseUrl/"
        return Retrofit.Builder()
            .baseUrl(root)
            .client(builder.build())
            .addConverterFactory(MoshiConverterFactory.create(moshi))
            .build()
            .create(CompanionService::class.java)
    }

    /**
     * Build OkHttp CertificatePinner from BuildConfig.CERT_PINS and/or a pin from pairing.
     * Format for CERT_PINS: "host|sha256/AAAA,other.host|sha256/BBBB"
     */
    fun buildCertificatePinner(baseUrl: String, pinSha256: String): CertificatePinner? {
        val host = try {
            java.net.URI(baseUrl).host
        } catch (_: Exception) {
            null
        } ?: return null

        val pins = mutableListOf<Pair<String, String>>()
        val configured = BuildConfig.CERT_PINS.trim()
        if (configured.isNotEmpty()) {
            configured.split(',').map { it.trim() }.filter { it.isNotEmpty() }.forEach { entry ->
                val parts = entry.split('|', limit = 2)
                if (parts.size == 2) {
                    pins += parts[0].trim() to parts[1].trim()
                }
            }
        }
        val fromPairing = pinSha256.trim()
        if (fromPairing.isNotEmpty()) {
            val pin = if (fromPairing.startsWith("sha256/")) fromPairing else "sha256/$fromPairing"
            pins += host to pin
        }
        if (pins.isEmpty()) return null

        val b = CertificatePinner.Builder()
        pins.forEach { (h, p) -> b.add(h, p) }
        return b.build()
    }
}
