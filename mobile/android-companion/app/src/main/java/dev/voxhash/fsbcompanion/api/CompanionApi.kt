package dev.voxhash.fsbcompanion.api

import dev.voxhash.fsbcompanion.model.CompanionHealth
import dev.voxhash.fsbcompanion.model.PortfolioSnapshot
import dev.voxhash.fsbcompanion.model.StrategiesResponse
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import retrofit2.http.GET
import retrofit2.http.Header
import java.util.concurrent.TimeUnit

interface CompanionService {
    @GET("api/v1/companion/health")
    suspend fun health(): CompanionHealth

    @GET("api/v1/companion/portfolio")
    suspend fun portfolio(@Header("Authorization") bearer: String): PortfolioSnapshot

    @GET("api/v1/companion/strategies")
    suspend fun strategies(@Header("Authorization") bearer: String): StrategiesResponse
}

object CompanionClientFactory {
    fun create(baseUrl: String, apiKey: String): CompanionService {
        val auth = Interceptor { chain ->
            val req = chain.request().newBuilder()
            if (apiKey.isNotBlank()) {
                req.header("Authorization", "Bearer $apiKey")
                req.header("X-API-Key", apiKey)
            }
            chain.proceed(req.build())
        }
        val client = OkHttpClient.Builder()
            .connectTimeout(10, TimeUnit.SECONDS)
            .readTimeout(15, TimeUnit.SECONDS)
            .addInterceptor(auth)
            .build()
        val root = if (baseUrl.endsWith("/")) baseUrl else "$baseUrl/"
        return Retrofit.Builder()
            .baseUrl(root)
            .client(client)
            .addConverterFactory(MoshiConverterFactory.create())
            .build()
            .create(CompanionService::class.java)
    }
}
