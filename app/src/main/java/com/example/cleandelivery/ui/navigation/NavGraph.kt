package com.example.cleandelivery.ui.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import com.example.cleandelivery.ui.screens.auth.LoginScreen
import com.example.cleandelivery.ui.screens.auth.OtpScreen
import com.example.cleandelivery.ui.screens.checkout.CheckoutScreen
import com.example.cleandelivery.ui.screens.home.HomeScreen
import com.example.cleandelivery.ui.screens.tracking.TrackingScreen

import com.example.cleandelivery.ui.screens.driver.DeliveryListScreen
import com.example.cleandelivery.ui.screens.driver.DriverHomeScreen
import com.example.cleandelivery.ui.screens.driver.DriverNavigationScreen
import com.example.cleandelivery.ui.screens.driver.EarningsScreen

sealed class Screen(val route: String) {
    object Login : Screen("login")
    object Otp : Screen("otp/{phone}") {
        fun createRoute(phone: String) = "otp/$phone"
    }
    object Home : Screen("home")
    object Checkout : Screen("checkout")
    object Tracking : Screen("tracking/{orderId}") {
        fun createRoute(orderId: String) = "tracking/$orderId"
    }

    // Driver Screens
    object DriverHome : Screen("driver_home")
    object DeliveryList : Screen("delivery_list")
    object DriverNavigation : Screen("driver_nav/{orderId}") {
        fun createRoute(orderId: String) = "driver_nav/$orderId"
    }
    object Earnings : Screen("earnings")
}

@Composable
fun NavGraph(navController: NavHostController) {
    NavHost(
        navController = navController,
        startDestination = Screen.Login.route
    ) {
        composable(Screen.Login.route) {
            LoginScreen(navController)
        }
        composable(Screen.Otp.route) { backStackEntry ->
            val phone = backStackEntry.arguments?.getString("phone") ?: ""
            OtpScreen(navController, phone)
        }
        composable(Screen.Home.route) {
            HomeScreen(navController)
        }
        composable(Screen.Checkout.route) {
            CheckoutScreen(navController)
        }
        composable(Screen.Tracking.route) { backStackEntry ->
            val orderId = backStackEntry.arguments?.getString("orderId") ?: ""
            TrackingScreen(navController, orderId)
        }

        // Driver Composables
        composable(Screen.DriverHome.route) {
            DriverHomeScreen(navController)
        }
        composable(Screen.DeliveryList.route) {
            DeliveryListScreen(navController)
        }
        composable(Screen.DriverNavigation.route) { backStackEntry ->
            val orderId = backStackEntry.arguments?.getString("orderId") ?: ""
            DriverNavigationScreen(navController, orderId)
        }
        composable(Screen.Earnings.route) {
            EarningsScreen(navController)
        }
    }
}
