package com.example.labtrack.network

import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.POST

data class ScanRequest(
    val tipo: String,      // "rfid" o "qr" -- CONFIRMAR contra IdentificacionService
    val valor: String,
    val lector_id: String? = null
)

data class AccesorioInfo(val id: Int, val nombre: String, val cantidad_default: Int)
data class EstudianteSesionInfo(val id: Int, val nombre: String, val matricula: String)
data class AccesorioPrestamoInfo(val id: Int, val nombre: String, val cantidad_prestada: Int)
data class PrestamoActivoInfo(
    val estudiante: EstudianteSesionInfo,
    val accesorios: List<AccesorioPrestamoInfo> = emptyList()
)

// Modelo "superset" que cubre IdentificacionResponse | QRScanResponse | QRUS06Response.
// Gson simplemente deja en null los campos que no vengan en esa respuesta puntual.
data class ScanResponse(
    val tipo: String,                              // "estudiante" o "equipo"
    // --- si tipo == "estudiante" (IdentificacionResponse) ---
    val estudiante_id: Int? = null,
    val nombre: String? = null,
    val matricula: String? = null,
    val uid_rfid: String? = null,
    val equipos_actuales: List<String> = emptyList(),
    val sesion_id: Int? = null,
    // --- si tipo == "equipo" (QRScanResponse / QRUS06Response) ---
    val equipo_id: Int? = null,
    val codigo: String? = null,
    val accesorios: List<AccesorioInfo> = emptyList(),
    val prestamo: PrestamoActivoInfo? = null,
    val estudiantes: List<EstudianteSesionInfo> = emptyList(),
    // --- comunes ---
    val estado: String? = null,
    val mensaje: String,
    val accion: String? = null
)

interface LabTrackApi {
    @POST("api/identificaciones/scan")
    suspend fun enviarScan(@Body body: ScanRequest): ScanResponse
}

object RetrofitClient {
    private const val BASE_URL = "https://labtrack-api-pvuh.onrender.com"

    val api: LabTrackApi by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(LabTrackApi::class.java)
    }
}
