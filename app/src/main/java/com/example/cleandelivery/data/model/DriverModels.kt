package com.example.cleandelivery.data.model

import com.google.gson.annotations.SerializedName

data class DriverLocationRequest(
    val latitude: Double,
    val longitude: Double
)

data class DriverStatusUpdateRequest(
    val status: String
)
