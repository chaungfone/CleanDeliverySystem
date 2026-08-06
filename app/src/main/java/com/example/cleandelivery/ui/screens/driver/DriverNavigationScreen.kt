package com.example.cleandelivery.ui.screens.driver

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Call
import androidx.compose.material.icons.filled.Email
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DriverNavigationScreen(
    navController: NavController,
    orderId: String
) {
    var showCompleteDialog by remember { mutableStateOf(false) }

    if (showCompleteDialog) {
        CompleteDeliveryDialog(
            onDismiss = { showCompleteDialog = false },
            onConfirm = {
                showCompleteDialog = false
                navController.popBackStack()
            }
        )
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Navigating to #${orderId.take(8)}") },
                navigationIcon = {
                    IconButton(onClick = { navController.popBackStack() }) {
                        Icon(Icons.Default.ArrowBack, contentDescription = null)
                    }
                }
            )
        },
        bottomBar = {
            Surface(tonalElevation = 8.dp) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    horizontalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    FloatingActionButton(
                        onClick = { /* Call Customer */ },
                        containerColor = MaterialTheme.colorScheme.secondaryContainer
                    ) {
                        Icon(Icons.Default.Call, contentDescription = null)
                    }
                    FloatingActionButton(
                        onClick = { /* SMS Customer */ },
                        containerColor = MaterialTheme.colorScheme.secondaryContainer
                    ) {
                        Icon(Icons.Default.Email, contentDescription = null)
                    }
                    Button(
                        onClick = { showCompleteDialog = true },
                        modifier = Modifier.weight(1f).height(56.dp)
                    ) {
                        Text("Arrived at Location")
                    }
                }
            }
        }
    ) { padding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .background(Color.LightGray),
            contentAlignment = Alignment.Center
        ) {
            Text("Google Maps Navigation View", fontWeight = FontWeight.Bold, fontSize = 20.sp)
        }
    }
}

@Composable
fun CompleteDeliveryDialog(
    onDismiss: () -> Unit,
    onConfirm: () -> Unit
) {
    var fullBottles by remember { mutableStateOf(1) }
    var emptyBottles by remember { mutableStateOf(1) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Complete Delivery") },
        text = {
            Column {
                Text("Verify quantities:")
                Spacer(modifier = Modifier.height(16.dp))
                
                QuantityRow(label = "Full Bottles Delivered", qty = fullBottles, onQtyChange = { fullBottles = it })
                QuantityRow(label = "Empty Bottles Collected", qty = emptyBottles, onQtyChange = { emptyBottles = it })
                
                Spacer(modifier = Modifier.height(16.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Checkbox(checked = true, onCheckedChange = {})
                    Text("Payment Collected (COD)")
                }
            }
        },
        confirmButton = {
            Button(onClick = onConfirm) {
                Text("Mark as Delivered")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        }
    )
}

@Composable
fun QuantityRow(label: String, qty: Int, onQtyChange: (Int) -> Unit) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(text = label, modifier = Modifier.weight(1f))
        Row(verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = { if (qty > 0) onQtyChange(qty - 1) }) {
                Text("-", fontSize = 20.sp, fontWeight = FontWeight.Bold)
            }
            Text(text = qty.toString(), modifier = Modifier.padding(horizontal = 8.dp))
            IconButton(onClick = { onQtyChange(qty + 1) }) {
                Text("+", fontSize = 20.sp, fontWeight = FontWeight.Bold)
            }
        }
    }
}
