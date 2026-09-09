package {{PACKAGE_NAME}}

interface DeviceHardware {
    // GPS Location
    fun startLocationUpdates(onLocationChanged: (lat: Double, lng: Double) -> Unit)
    fun stopLocationUpdates()

    // 3-Axis Sensors (Accelerometer / Gyroscope / Magnetometer)
    fun startAccelerometerUpdates(onSensorChanged: (x: Float, y: Float, z: Float) -> Unit)
    fun stopAccelerometerUpdates()
}

expect fun getDeviceHardware(context: Any? = null): DeviceHardware
