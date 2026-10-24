package dev.voxhash.fsbcompanion.ui

import android.graphics.Bitmap
import com.google.zxing.BinaryBitmap
import com.google.zxing.MultiFormatReader
import com.google.zxing.RGBLuminanceSource
import com.google.zxing.common.HybridBinarizer
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import dev.voxhash.fsbcompanion.model.PairingQrPayload

object PairingParser {
    private val moshi = Moshi.Builder().add(KotlinJsonAdapterFactory()).build()
    private val adapter = moshi.adapter(PairingQrPayload::class.java)

    fun parseQrText(raw: String): PairingQrPayload? {
        val text = raw.trim()
        if (text.isEmpty()) return null
        return try {
            adapter.fromJson(text)
        } catch (_: Exception) {
            null
        }
    }

    fun decodeBitmap(bitmap: Bitmap): String? {
        return try {
            val width = bitmap.width
            val height = bitmap.height
            val pixels = IntArray(width * height)
            bitmap.getPixels(pixels, 0, width, 0, 0, width, height)
            val source = RGBLuminanceSource(width, height, pixels)
            val binary = BinaryBitmap(HybridBinarizer(source))
            MultiFormatReader().decode(binary).text
        } catch (_: Exception) {
            null
        }
    }
}
