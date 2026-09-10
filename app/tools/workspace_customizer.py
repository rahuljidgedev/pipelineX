import os
import re
import shutil
from app.tools.workspace_registry import register_app
from app.core.constants import WORKSPACE_DIR

def slugify(text: str) -> str:
    """Convert arbitrary text into a clean alphanumeric slug (no special chars)."""
    # Lowercase, replace non-alphanumeric with spaces, then strip and collapse spaces
    clean = re.sub(r'[^a-zA-Z0-9\s]', '', text.lower())
    words = clean.strip().split()
    slug = "".join(words)
    if not slug or slug[0].isdigit():
        slug = "app" + slug
    return slug

def generate_project_metadata(idea: str):
    """Generate clean app title, package name, and namespace from the user's idea."""
    # Fallback default if empty
    if not idea or not idea.strip():
        idea = "kmpapp"
        
    slug = slugify(idea)
    # Ensure it's not empty after cleaning
    if not slug:
        slug = "kmpapp"
        
    # Cap package name segment length
    if len(slug) > 30:
        slug = slug[:30]
        
    app_title = " ".join([word.capitalize() for word in re.sub(r'[^a-zA-Z0-9\s]', ' ', idea).strip().split()])
    if not app_title:
        app_title = "KMP Application"
        
    package_name = f"com.example.{slug}"
    namespace = f"com.example.{slug}"
    
    return {
        "app_id": slug,
        "app_title": app_title,
        "package_name": package_name,
        "namespace": namespace
    }

def customize_file_content(filepath: str, metadata: dict):
    """Replace all double-brace placeholders with actual project metadata."""
    if not os.path.exists(filepath):
        return
        
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        content = content.replace("{{APP_NAME}}", metadata["app_title"])
        content = content.replace("{{PACKAGE_NAME}}", metadata["package_name"])
        content = content.replace("{{NAMESPACE}}", metadata["namespace"])
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        print(f"├─ [CUSTOMIZER] ⚠️ Failed to customize {filepath}: {e}")

def seed_custom_workspace(idea: str, target_workspace: str = WORKSPACE_DIR):
    """
    Copy KMP Golden Template files to the target workspace and customize them
    according to the dynamic project requirements generated from the user's idea.
    """
    metadata = generate_project_metadata(idea)
    print(f"├─ [CUSTOMIZER] 🚀 Seeding customized workspace for: '{idea}'")
    print(f"├─ [CUSTOMIZER]    App Title:    {metadata['app_title']}")
    print(f"├─ [CUSTOMIZER]    Package Name: {metadata['package_name']}")
    print(f"├─ [CUSTOMIZER]    Namespace:    {metadata['namespace']}")
    
    # 1. Clear ONLY the target app's directory to ensure a pristine seed for this app
    app_dir = os.path.join(target_workspace, "apps", metadata["app_id"])
    if os.path.exists(app_dir):
        for filename in os.listdir(app_dir):
            file_path = os.path.join(app_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')
    else:
        os.makedirs(app_dir, exist_ok=True)
    
    # 2. Source template base path
    template_path = "app/resources/kmp_golden_template"
    if not os.path.exists(template_path):
        print(f"├─ [CUSTOMIZER] ⚠️ Golden template not found at {template_path}. Creating fallback template structure...")
        _create_fallback_golden_template(template_path)
        
    # 3. Copy files from template to workspace
    # Root files go to target_workspace, composeApp files go to apps/{app_id}
    for root, dirs, files in os.walk(template_path):
        rel_path = os.path.relpath(root, template_path)
        
        # Determine destination directory
        if rel_path == "." or not rel_path.startswith("composeApp"):
            dest_dir = os.path.join(target_workspace, rel_path) if rel_path != "." else target_workspace
        else:
            # Map "composeApp" to "apps/{app_id}"
            remapped_path = rel_path.replace("composeApp", "", 1).lstrip(os.sep)
            dest_dir = os.path.join(app_dir, remapped_path)
            
        os.makedirs(dest_dir, exist_ok=True)
        
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(dest_dir, file)
            
            # Copy file (only overwrite root files if they don't exist, to preserve global state, except settings.gradle.kts which we dynamically rewrite)
            if rel_path == "." or not rel_path.startswith("composeApp"):
                if file != "settings.gradle.kts" and not os.path.exists(dest_file):
                    shutil.copy2(src_file, dest_file)
            else:
                shutil.copy2(src_file, dest_file)
            
            # Customize content (replace placeholders) for the files we just copied/exist
            if os.path.exists(dest_file):
                customize_file_content(dest_file, metadata)
                
    # 3.5 Dynamically rewrite settings.gradle.kts for Ghost Monorepo
    settings_content = f"""pluginManagement {{
    repositories {{
        google()
        mavenCentral()
        gradlePluginPortal()
    }}
}}
dependencyResolutionManagement {{
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {{
        google()
        mavenCentral()
    }}
}}
rootProject.name = "PipelineX-Factory"
include(":shared-core")
include(":apps:{metadata['app_id']}")
"""
    with open(os.path.join(target_workspace, "settings.gradle.kts"), "w") as f:
        f.write(settings_content)
            
    # 4. Check for hardware capabilities requested in the idea and write sub-manifest features
    idea_lower = idea.lower()
    permissions = []
    features = []
    
    if any(k in idea_lower for k in ["gps", "location", "map", "coordinate", "tracker", "navigation"]):
        permissions.append("android.permission.ACCESS_FINE_LOCATION")
        permissions.append("android.permission.ACCESS_COARSE_LOCATION")
        features.append("android.hardware.location.gps")
        print("├─ [CUSTOMIZER] 🛰️ Detected Location/GPS requirements.")
        
    if any(k in idea_lower for k in ["camera", "photo", "picture", "video", "capture"]):
        permissions.append("android.permission.CAMERA")
        features.append("android.hardware.camera")
        print("├─ [CUSTOMIZER] 📷 Detected Camera requirements.")
        
    if permissions or features:
        manifest_path = os.path.join(app_dir, "src", "androidMain", "AndroidManifest-features.xml")
        os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
        
        perm_lines = "\n".join([f'    <uses-permission android:name="{p}" />' for p in permissions])
        feat_lines = "\n".join([f'    <uses-feature android:name="{f}" android:required="false" />' for f in features])
        
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(f"""<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="{metadata['package_name']}">
{perm_lines}
{feat_lines}
</manifest>""")
        print(f"├─ [CUSTOMIZER] 📝 Dynamic AndroidManifest-features.xml written with permissions: {permissions}")

    # Register the app in the global registry
    register_app(metadata["app_id"], metadata["package_name"], metadata["app_title"])

    print(f"├─ [CUSTOMIZER] ✅ Golden Template seeded and customized in '{app_dir}'!")
    return metadata

def _create_fallback_golden_template(path: str):
    """Creates a basic compilable Golden Template structure if it's missing."""
    os.makedirs(path, exist_ok=True)
    
    # settings.gradle.kts
    with open(os.path.join(path, "settings.gradle.kts"), "w") as f:
        f.write('''pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = "{{APP_NAME}}"
include(":composeApp")
''')

    # build.gradle.kts (Project level)
    with open(os.path.join(path, "build.gradle.kts"), "w") as f:
        f.write('''plugins {
    id("com.android.application") version "8.2.2" apply false
    id("com.android.library") version "8.2.2" apply false
    kotlin("multiplatform") version "1.9.20" apply false
    id("org.jetbrains.compose") version "1.6.0" apply false
}
''')

    # gradle.properties
    with open(os.path.join(path, "gradle.properties"), "w") as f:
        f.write('''org.gradle.jvmargs=-Xmx2048m -XX:MaxMetaspaceSize=512m
''')

    # composeApp directory
    os.makedirs(os.path.join(path, "composeApp"), exist_ok=True)
    
    # composeApp/build.gradle.kts
    with open(os.path.join(path, "composeApp", "build.gradle.kts"), "w") as f:
        f.write('''plugins {
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
        minSdk = 21
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
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
''')

    # composeApp src layout
    os.makedirs(os.path.join(path, "composeApp", "src", "androidMain", "kotlin"), exist_ok=True)
    os.makedirs(os.path.join(path, "composeApp", "src", "commonMain", "kotlin"), exist_ok=True)
    
    # composeApp/src/androidMain/AndroidManifest.xml (Zero-Resource Paradigm A)
    with open(os.path.join(path, "composeApp", "src", "androidMain", "AndroidManifest.xml"), "w") as f:
        f.write('''<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application
        android:allowBackup="true"
        android:icon="@android:drawable/sym_def_app_icon"
        android:label="{{APP_NAME}}"
        android:supportsRtl="true"
        android:theme="@android:style/Theme.Material.NoActionBar">
        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
''')

    # composeApp/src/androidMain/kotlin/MainActivity.kt
    with open(os.path.join(path, "composeApp", "src", "androidMain", "kotlin", "MainActivity.kt"), "w") as f:
        f.write('''package {{PACKAGE_NAME}}

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            App()
        }
    }
}
''')

    # composeApp/src/commonMain/kotlin/App.kt
    with open(os.path.join(path, "composeApp", "src", "commonMain", "kotlin", "App.kt"), "w") as f:
        f.write('''package {{PACKAGE_NAME}}

import androidx.compose.runtime.Composable
import androidx.compose.material3.Text
import androidx.compose.material3.MaterialTheme
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier

@Composable
fun App() {
    MaterialTheme {
        Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            Text(text = "Hello from {{APP_NAME}}!")
        }
    }
}
''')

    # composeApp/src/commonMain/kotlin/Hardware.kt
    with open(os.path.join(path, "composeApp", "src", "commonMain", "kotlin", "Hardware.kt"), "w") as f:
        f.write('''package {{PACKAGE_NAME}}

interface DeviceHardware {
    fun startLocationUpdates(onLocationChanged: (lat: Double, lng: Double) -> Unit)
    fun stopLocationUpdates()
    fun startAccelerometerUpdates(onSensorChanged: (x: Float, y: Float, z: Float) -> Unit)
    fun stopAccelerometerUpdates()
}

expect fun getDeviceHardware(context: Any? = null): DeviceHardware
''')

    # composeApp/src/androidMain/kotlin/Hardware.kt
    with open(os.path.join(path, "composeApp", "src", "androidMain", "kotlin", "Hardware.kt"), "w") as f:
        f.write('''package {{PACKAGE_NAME}}

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.Bundle

class AndroidDeviceHardware(private val context: Context) : DeviceHardware, SensorEventListener, LocationListener {
    private val sensorManager = context.getSystemService(Context.SENSOR_SERVICE) as SensorManager
    private val locationManager = context.getSystemService(Context.LOCATION_SERVICE) as LocationManager
    private var accelCallback: ((Float, Float, Float) -> Unit)? = null
    private var locationCallback: ((Double, Double) -> Unit)? = null

    override fun startLocationUpdates(onLocationChanged: (Double, Double) -> Unit) {
        locationCallback = onLocationChanged
        try {
            locationManager.requestLocationUpdates(LocationManager.GPS_PROVIDER, 1000L, 1f, this)
            locationManager.requestLocationUpdates(LocationManager.NETWORK_PROVIDER, 1000L, 1f, this)
        } catch (e: SecurityException) {
            println("Security Exception: ${e.message}")
        } catch (e: Exception) {
            println("Exception: ${e.message}")
        }
    }

    override fun stopLocationUpdates() {
        locationManager.removeUpdates(this)
        locationCallback = null
    }

    override fun startAccelerometerUpdates(onSensorChanged: (Float, Float, Float) -> Unit) {
        accelCallback = onSensorChanged
        val accel = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
        if (accel != null) {
            sensorManager.registerListener(this, accel, SensorManager.SENSOR_DELAY_NORMAL)
        }
    }

    override fun stopAccelerometerUpdates() {
        sensorManager.unregisterListener(this)
        accelCallback = null
    }

    override fun onSensorChanged(event: SensorEvent?) {
        if (event != null && event.sensor.type == Sensor.TYPE_ACCELEROMETER) {
            accelCallback?.invoke(event.values[0], event.values[1], event.values[2])
        }
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}
    override fun onLocationChanged(location: Location) {
        locationCallback?.invoke(location.latitude, location.longitude)
    }

    @Deprecated("Deprecated")
    override fun onStatusChanged(provider: String?, status: Int, extras: Bundle?) {}
    override fun onProviderEnabled(provider: String) {}
    override fun onProviderDisabled(provider: String) {}
}

actual fun getDeviceHardware(context: Any?): DeviceHardware {
    val androidContext = context as? Context ?: throw IllegalArgumentException("Android Context required")
    return AndroidDeviceHardware(androidContext)
}
''')
