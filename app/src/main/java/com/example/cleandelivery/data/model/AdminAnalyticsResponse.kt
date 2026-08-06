package com.example.cleandelivery.data.model

import com.google.gson.annotations.SerializedName

data class AdminAnalyticsResponse(
    val period: String,
    @SerializedName("start_date")
    val startDate: String,
    @SerializedName("total_revenue")
    val totalRevenue: String,
    @SerializedName("delivered_volume")
    val deliveredVolume: Int,
    @SerializedName("pending_deliveries")
    val pendingDeliveries: Int,
    @SerializedName("active_drivers")
    val activeDrivers: Int
)
