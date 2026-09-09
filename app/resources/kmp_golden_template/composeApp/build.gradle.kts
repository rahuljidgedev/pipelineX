plugins {
    id("com.android.application")
    kotlin("multiplatform")
    id("org.jetbrains.compose")
    kotlin("plugin.serialization") version "1.9.20"
}

android {
    compileSdk = 34
    namespace = "{{NAMESPACE}}"

    defaultConfig {
        applicationId = "{{PACKAGE_NAME}}"
        minSdk = 24
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

kotlin {
    androidTarget()

    sourceSets {
        val commonMain by getting {
            dependencies {
                implementation(compose.runtime)
                implementation(compose.foundation)
                implementation(compose.material)
                implementation(compose.material3)
                implementation(compose.ui)
                implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3")
                implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.0")
                implementation("io.ktor:ktor-client-core:2.3.7")
                implementation("io.ktor:ktor-client-content-negotiation:2.3.7")
                implementation("io.ktor:ktor-serialization-kotlinx-json:2.3.7")
                
                // #DYNAMIC_DEPENDENCIES_INJECTION_POINT#
            }
        }
        val androidMain by getting {
            dependencies {
                implementation("androidx.activity:activity-compose:1.7.2")
                implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.6.2")
                implementation("io.ktor:ktor-client-okhttp:2.3.7")
            }
        }
    }
}
