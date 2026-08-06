package com.example.cleandelivery.ui.screens.driver

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavController
import com.example.cleandelivery.ui.navigation.Screen
import com.example.cleandelivery.ui.viewmodel.DriverViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DriverHomeScreen(
    navController: NavController,
    viewModel: DriverViewModel = hiltViewModel()
) {
    val isOnline by viewModel.isOnline.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Driver Dashboard") },
                actions = {
                    IconButton(onClick = { navController.navigate(Screen.Earnings.route) }) {
                        Icon(Icons.Default.ShoppingCart, contentDescription = "Earnings")
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // Online/Offline Toggle Card
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(
                    containerColor = if (isOnline) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surfaceVariant
                )
            ) {
                Row(
                    modifier = Modifier
                        .padding(16.dp)
                        .fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Column {
                        Text(
                            text = if (isOnline) "You are Online" else "You are Offline",
                            fontWeight = FontWeight.Bold,
                            fontSize = 18.sp
                        )
                        Text(
                            text = if (isOnline) "Accepting delivery requests" else "Shift not started",
                            style = MaterialTheme.typography.bodySmall
                        )
                    }
                    Switch(
                        checked = isOnline,
                        onCheckedChange = { viewModel.toggleOnlineStatus() }
                    )
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            // Shift Summary Section
            Text(
                text = "Today's Summary",
                fontWeight = FontWeight.Bold,
                fontSize = 20.sp,
                modifier = Modifier.align(Alignment.Start)
            )
            
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                SummaryCard(
                    modifier = Modifier.weight(1f),
                    title = "Delivered",
                    value = "12",
                    icon = Icons.Default.CheckCircle
                )
                SummaryCard(
                    modifier = Modifier.weight(1f),
                    title = "Empties",
                    value = "8",
                    icon = Icons.Default.Refresh
                )
            }

            Spacer(modifier = Modifier.height(24.dp))

            // Navigation Buttons
            Button(
                onClick = { navController.navigate(Screen.DeliveryList.route) },
                modifier = Modifier.fillMaxWidth(),
                shape = MaterialTheme.shapes.medium
            ) {
                Icon(Icons.Default.List, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text("View Delivery Jobs")
            }
        }
    }
}

@Composable
fun SummaryCard(
    modifier: Modifier = Modifier,
    title: String,
    value: String,
    icon: ImageVector
) {
    ElevatedCard(modifier = modifier) {
        Column(
            modifier = Modifier.padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Icon(icon, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
            Text(text = value, fontSize = 24.sp, fontWeight = FontWeight.ExtraBold)
            Text(text = title, style = MaterialTheme.typography.labelMedium)
        }
    }
}
