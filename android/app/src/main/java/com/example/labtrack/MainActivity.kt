package com.example.labtrack

import android.app.PendingIntent
import android.content.Intent
import android.nfc.NfcAdapter
import android.nfc.Tag
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.lifecycleScope
import com.example.labtrack.network.RetrofitClient
import com.example.labtrack.network.ScanRequest
import com.example.labtrack.ui.theme.LABTRACKTheme
import com.google.mlkit.vision.barcode.common.Barcode
import com.google.mlkit.vision.codescanner.GmsBarcodeScannerOptions
import com.google.mlkit.vision.codescanner.GmsBarcodeScanning
import kotlinx.coroutines.launch
import retrofit2.HttpException

class MainActivity : ComponentActivity() {

    private var nfcAdapter: NfcAdapter? = null

    private var uid by mutableStateOf("")
    private var equipo by mutableStateOf("")

    private var nfcStatus by mutableStateOf("Esperando tarjeta")
    private var qrStatus by mutableStateOf("Sin código")
    private var backendMensaje by mutableStateOf("")

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        enableEdgeToEdge()

        nfcAdapter = NfcAdapter.getDefaultAdapter(this)

        setContent {
            LABTRACKTheme {

                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {

                    Column(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(24.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {

                        Spacer(modifier = Modifier.height(30.dp))

                        Text(
                            text = "LABTRACK",
                            fontSize = 30.sp,
                            fontWeight = FontWeight.Bold
                        )

                        Text(
                            text = "Captura de identificadores",
                            fontSize = 15.sp,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )

                        Spacer(modifier = Modifier.height(35.dp))

                        // TARJETA NFC
                        Card(
                            modifier = Modifier.fillMaxWidth(),
                            shape = RoundedCornerShape(20.dp),
                            elevation = CardDefaults.cardElevation(
                                defaultElevation = 4.dp
                            )
                        ) {

                            Column(
                                modifier = Modifier.padding(20.dp)
                            ) {

                                Row(
                                    verticalAlignment = Alignment.CenterVertically
                                ) {

                                    Box(
                                        modifier = Modifier
                                            .size(48.dp)
                                            .clip(RoundedCornerShape(12.dp))
                                            .background(
                                                MaterialTheme.colorScheme.primaryContainer
                                            ),
                                        contentAlignment = Alignment.Center
                                    ) {
                                        Text(
                                            text = "NFC",
                                            fontSize = 12.sp,
                                            fontWeight = FontWeight.Bold
                                        )
                                    }

                                    Spacer(modifier = Modifier.size(14.dp))

                                    Column {
                                        Text(
                                            text = "Estudiante",
                                            fontSize = 18.sp,
                                            fontWeight = FontWeight.Bold
                                        )

                                        Text(
                                            text = nfcStatus,
                                            fontSize = 13.sp,
                                            color = MaterialTheme.colorScheme.onSurfaceVariant
                                        )
                                    }
                                }

                                Spacer(modifier = Modifier.height(18.dp))

                                Text(
                                    text = if (uid.isEmpty()) {
                                        "Acerca una tarjeta NFC"
                                    } else {
                                        uid
                                    },
                                    fontSize = 18.sp,
                                    fontWeight = FontWeight.Medium
                                )
                            }
                        }

                        Spacer(modifier = Modifier.height(18.dp))

                        // TARJETA QR
                        Card(
                            modifier = Modifier.fillMaxWidth(),
                            shape = RoundedCornerShape(20.dp),
                            elevation = CardDefaults.cardElevation(
                                defaultElevation = 4.dp
                            )
                        ) {

                            Column(
                                modifier = Modifier.padding(20.dp)
                            ) {

                                Row(
                                    verticalAlignment = Alignment.CenterVertically
                                ) {

                                    Box(
                                        modifier = Modifier
                                            .size(48.dp)
                                            .clip(RoundedCornerShape(12.dp))
                                            .background(
                                                MaterialTheme.colorScheme.secondaryContainer
                                            ),
                                        contentAlignment = Alignment.Center
                                    ) {
                                        Text(
                                            text = "QR",
                                            fontSize = 12.sp,
                                            fontWeight = FontWeight.Bold
                                        )
                                    }

                                    Spacer(modifier = Modifier.size(14.dp))

                                    Column {
                                        Text(
                                            text = "Equipo",
                                            fontSize = 18.sp,
                                            fontWeight = FontWeight.Bold
                                        )

                                        Text(
                                            text = qrStatus,
                                            fontSize = 13.sp,
                                            color = MaterialTheme.colorScheme.onSurfaceVariant
                                        )
                                    }
                                }

                                Spacer(modifier = Modifier.height(18.dp))

                                Text(
                                    text = if (equipo.isEmpty()) {
                                        "Ningún equipo escaneado"
                                    } else {
                                        equipo
                                    },
                                    fontSize = 18.sp,
                                    fontWeight = FontWeight.Medium
                                )

                                Spacer(modifier = Modifier.height(16.dp))

                                Button(
                                    onClick = {
                                        escanearQR()
                                    },
                                    modifier = Modifier.fillMaxWidth(),
                                    shape = RoundedCornerShape(12.dp)
                                ) {
                                    Text("ESCANEAR QR")
                                }
                            }
                        }

                        if (backendMensaje.isNotEmpty()) {
                            Spacer(modifier = Modifier.height(18.dp))
                            Text(
                                text = backendMensaje,
                                fontSize = 14.sp,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }

                        Spacer(modifier = Modifier.height(25.dp))

                        Text(
                            text = "Los identificadores se enviarán a LABTRACK",
                            fontSize = 13.sp,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
        }
    }

    private fun escanearQR() {

        val options = GmsBarcodeScannerOptions.Builder()
            .setBarcodeFormats(Barcode.FORMAT_QR_CODE)
            .enableAutoZoom()
            .build()

        val scanner = GmsBarcodeScanning.getClient(
            this,
            options
        )

        scanner.startScan()
            .addOnSuccessListener { barcode ->

                barcode.rawValue?.let { resultado ->

                    equipo = resultado
                    qrStatus = "Código detectado"
                    enviarScan(tipo = "qr", valor = resultado)
                }
            }
            .addOnCanceledListener {

                qrStatus = "Escaneo cancelado"
            }
            .addOnFailureListener { error ->

                qrStatus = "Error al escanear"
            }
    }

    private fun enviarScan(tipo: String, valor: String) {
        lifecycleScope.launch {
            try {
                val respuesta = RetrofitClient.api.enviarScan(
                    ScanRequest(tipo = tipo, valor = valor, lector_id = "app-android")
                )
                backendMensaje = if (respuesta.estado == "no_registrado") {
                    "Tarjeta no registrada: ${respuesta.mensaje}"
                } else {
                    respuesta.mensaje
                }
            } catch (e: HttpException) {
                val cuerpoError = e.response()?.errorBody()?.string()
                backendMensaje = "Error del servidor (${e.code()}): $cuerpoError"
            } catch (e: Exception) {
                backendMensaje = "Error de conexión: ${e.message}"
            }
        }
    }

    override fun onResume() {
        super.onResume()

        val adapter = nfcAdapter ?: return

        val intent = Intent(
            this,
            javaClass
        ).apply {
            addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP)
        }

        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            intent,
            PendingIntent.FLAG_MUTABLE
        )

        adapter.enableForegroundDispatch(
            this,
            pendingIntent,
            null,
            null
        )
    }

    override fun onPause() {
        super.onPause()

        nfcAdapter?.disableForegroundDispatch(this)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)

        val tag: Tag? =
            intent.getParcelableExtra(NfcAdapter.EXTRA_TAG)

        tag?.id?.let { bytes ->

            uid = bytes.joinToString(":") {
                "%02X".format(it)
            }

            nfcStatus = "Tarjeta detectada"
            enviarScan(tipo = "rfid", valor = uid)
        }
    }
}