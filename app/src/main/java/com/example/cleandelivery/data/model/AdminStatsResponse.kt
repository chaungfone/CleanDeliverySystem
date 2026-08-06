package com.example.cleandelivery.data.model

import com.google.gson.annotations.SerializedName

/**
 * Maps the backend `app/api/v1/endpoints/admin.py::dashboard_stats` payload.
 *
 * `todayRevenue` is serialised by the backend as a String (Decimal formatting).
 */
data class AdminStatsResponse(
    @SerializedName("today_total_orders")
    val todayTotalOrders: Int = 0,
    @SerializedName("today_revenue")
    val todayRevenue: String = "0",
    @SerializedName("pending_deliveries")
    val pendingDeliveries: Int = 0,
    @SerializedName("total_drivers")
    val totalDrivers: Int = 0,
    @SerializedName("active_drivers")
    val activeDrivers: Int = 0,
    @SerializedName("low_stock_products")
    val lowStockProducts: List<LowStockProduct> = emptyList()
)

data class LowStockProduct(
    val id: String,
    val name: String,
    @SerializedName("stock_quantity")
    val stockQuantity: Int = 0
)