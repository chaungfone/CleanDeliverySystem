package com.example.cleandelivery.data.model

import com.google.gson.annotations.SerializedName

/**
 * Maps the backend `app/models/product.py::ProductResponse`.
 *
 * Prices are serialised by FastAPI as JSON numbers (Double).
 */
data class ProductDto(
    val id: String,
    val name: String,
    val description: String? = null,
    val price: Double = 0.0,
    @SerializedName("deposit_fee")
    val depositFee: Double = 0.0,
    @SerializedName("stock_quantity")
    val stockQuantity: Int = 0,
    @SerializedName("created_at")
    val createdAt: String
)