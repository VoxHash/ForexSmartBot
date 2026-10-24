package dev.voxhash.fsbcompanion.ui

import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy
import com.google.zxing.BarcodeFormat
import com.google.zxing.BinaryBitmap
import com.google.zxing.DecodeHintType
import com.google.zxing.MultiFormatReader
import com.google.zxing.PlanarYUVLuminanceSource
import com.google.zxing.common.HybridBinarizer
import java.nio.ByteBuffer

/**
 * CameraX ImageAnalysis → ZXing QR decode (no ML Kit / Play Services).
 */
class QrAnalyzer(
    private val onQr: (String) -> Unit,
) : ImageAnalysis.Analyzer {
    private val reader = MultiFormatReader().apply {
        setHints(
            mapOf(
                DecodeHintType.POSSIBLE_FORMATS to listOf(BarcodeFormat.QR_CODE),
                DecodeHintType.TRY_HARDER to true,
            ),
        )
    }
    @Volatile private var done = false

    override fun analyze(image: ImageProxy) {
        if (done) {
            image.close()
            return
        }
        try {
            val y = image.planes[0].buffer.toByteArray()
            val source = PlanarYUVLuminanceSource(
                y,
                image.width,
                image.height,
                0,
                0,
                image.width,
                image.height,
                false,
            )
            val text = reader.decodeWithState(BinaryBitmap(HybridBinarizer(source))).text
            if (!text.isNullOrBlank()) {
                done = true
                onQr(text)
            }
        } catch (_: Exception) {
            // No QR in this frame
        } finally {
            reader.reset()
            image.close()
        }
    }

    private fun ByteBuffer.toByteArray(): ByteArray {
        rewind()
        val data = ByteArray(remaining())
        get(data)
        return data
    }
}
