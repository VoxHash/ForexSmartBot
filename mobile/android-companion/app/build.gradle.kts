plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    namespace = "dev.voxhash.fsbcompanion"
    compileSdk = 35

    defaultConfig {
        applicationId = "dev.voxhash.fsbcompanion"
        minSdk = 29
        targetSdk = 35
        versionCode = 3
        versionName = "0.3.0"
        buildConfigField("String", "DEFAULT_BASE_URL", "\"http://127.0.0.1:8080\"")
        // Comma-separated host|sha256/BASE64 pins. Override via -PFSB_CERT_PINS=...
        val pins = (project.findProperty("FSB_CERT_PINS") as String?)?.trim().orEmpty()
        buildConfigField("String", "CERT_PINS", "\"${pins.replace("\"", "\\\"")}\"")
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
            // Production pin defaults: require FSB_CERT_PINS for release store builds.
            // Pairing QR pin still applies when CERT_PINS is empty (LAN / self-host).
            val releasePins = (project.findProperty("FSB_CERT_PINS") as String?)?.trim().orEmpty()
            buildConfigField("String", "CERT_PINS", "\"${releasePins.replace("\"", "\\\"")}\"")
        }
        debug {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
    buildFeatures {
        buildConfig = true
        compose = true
    }
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2024.10.00")
    implementation(composeBom)
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.activity:activity-compose:1.9.3")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.6")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.6")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.8.1")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.retrofit2:retrofit:2.11.0")
    implementation("com.squareup.retrofit2:converter-moshi:2.11.0")
    implementation("com.squareup.moshi:moshi-kotlin:1.15.1")
    // ZXing — GrapheneOS-friendly QR decode (no Play Services / ML Kit)
    implementation("com.google.zxing:core:3.5.3")
    // Live CameraX QR (no GMS)
    val cameraX = "1.3.4"
    implementation("androidx.camera:camera-core:$cameraX")
    implementation("androidx.camera:camera-camera2:$cameraX")
    implementation("androidx.camera:camera-lifecycle:$cameraX")
    implementation("androidx.camera:camera-view:$cameraX")
    // Encrypted local session + portfolio cache
    implementation("androidx.security:security-crypto:1.1.0-alpha06")
}
