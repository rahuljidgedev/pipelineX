package {{PACKAGE_NAME}}

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
            println("Security Exception starting location updates: ${e.message}")
        } catch (e: Exception) {
            println("Exception starting location updates: ${e.message}")
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

    // SensorEventListener
    override fun onSensorChanged(event: SensorEvent?) {
        if (event != null && event.sensor.type == Sensor.TYPE_ACCELEROMETER) {
            accelCallback?.invoke(event.values[0], event.values[1], event.values[2])
        }
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}

    // LocationListener
    override fun onLocationChanged(location: Location) {
        locationCallback?.invoke(location.latitude, location.longitude)
    }

    @Deprecated("Deprecated in Java")
    override fun onStatusChanged(provider: String?, status: Int, extras: Bundle?) {}
    override fun onProviderEnabled(provider: String) {}
    override fun onProviderDisabled(provider: String) {}
}

actual fun getDeviceHardware(context: Any?): DeviceHardware {
    val androidContext = context as? Context ?: throw IllegalArgumentException("Android Context required")
    return AndroidDeviceHardware(androidContext)
}
