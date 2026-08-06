package com.example.cleandelivery.ui.screens.home

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavController
import com.example.cleandelivery.data.model.ProductDto
import com.example.cleandelivery.ui.navigation.Screen
import com.example.cleandelivery.ui.viewmodel.HomeViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    navController: NavController,
    viewModel: HomeViewModel = hiltViewModel()
) {
    val products by viewModel.products.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()
    val cartItems = remember { mutableStateMapOf<String, Int>() }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Water Delivery") },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    titleContentColor = MaterialTheme.colorScheme.onPrimary
                )
            )
        },
        floatingActionButton = {
            if (cartItems.values.sum() > 0) {
                ExtendedFloatingActionButton(
                    onClick = { navController.navigate(Screen.Checkout.route) },
                    icon = { Icon(Icons.Default.Check, contentDescription = null) },
                    text = { Text("Checkout (${cartItems.values.sum()})") }
                )
            }
        }
    ) { padding ->
        if (isLoading && products.isEmpty()) {
            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator()
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
            ) {
                items(products) { product ->
                    ProductItem(
                        product = product,
                        quantity = cartItems[product.id] ?: 0,
                        onQuantityChange = { qty ->
                            if (qty > 0) cartItems[product.id] = qty else cartItems.remove(product.id)
                        }
                    )
                }
            }
        }
    }
}

@Composable
fun ProductItem(
    product: ProductDto,
    quantity: Int,
    onQuantityChange: (Int) -> Unit
) {
    ElevatedCard(
        modifier = Modifier
            .fillMaxWidth()
            .padding(8.dp)
    ) {
        Row(
            modifier = Modifier
                .padding(16.dp)
                .fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(text = product.name, fontWeight = FontWeight.Bold, fontSize = 18.sp)
                Text(text = "${product.price} MMK", color = MaterialTheme.colorScheme.secondary)
            }
            
            Row(verticalAlignment = Alignment.CenterVertically) {
                IconButton(onClick = { if (quantity > 0) onQuantityChange(quantity - 1) }) {
                    Text("-", fontSize = 24.sp, fontWeight = FontWeight.Bold)
                }
                Text(text = quantity.toString(), modifier = Modifier.padding(horizontal = 8.dp))
                IconButton(onClick = { onQuantityChange(quantity + 1) }) {
                    Icon(Icons.Default.Add, contentDescription = null)
                }
            }
        }
    }
}
