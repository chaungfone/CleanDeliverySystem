package com.example.cleandelivery.data.model

import com.google.gson.annotations.SerializedName

/**
 * Maps the backend `app/models/order.py` schemas:
 * `OrderItemCreate`, `OrderCreate`, `OrderItemSchema`, `OrderResponse`.
 *
 * `status` is one of: PENDING | CONFIRMED | ASSIGNED | IN_TRANSIT | DELIVERED | CANCELLED.
 * `payment_method` is one of: COD | KPAY | WAVE_PAY | OTHER.
 */
data class OrderCreateRequest(
    @SerializedName("address_id")
    val addressId: String,
    @SerializedName("payment_method")
    val paymentMethod: String = "COD",
    @SerializedName("empty_bottles_returned")
    val emptyBottlesReturned: Int = 0,
    val items: List<OrderItemCreateRequest>
)

data class OrderItemCreateRequest(
    @SerializedName("product_id")
    val productId: String,
    val quantity: Int,
    @SerializedName("unit_price")
    val unitPrice: Double? = null
)

data class OrderDto(
    val id: String,
    @SerializedName("customer_id")
    val customerId: String,
    @SerializedName("driver_id")
    val driverId: String? = null,
    @SerializedName("address_id")
    val addressId: String,
    val status: String,
    @SerializedName("total_amount")
    val totalAmount: Double = 0.0,
    @SerializedName("payment_status")
    val paymentStatus: String,
    @SerializedName("payment_method")
    val paymentMethod: String,
    @SerializedName("empty_bottles_returned")
    val emptyBottlesReturned: Int = 0,
    @SerializedName("created_at")
    val createdAt: String,
    val items: List<OrderItemDto> = emptyList()
)

data class OrderItemDto(
    val id: String,
    @SerializedName("order_id")
    val orderId: String,
    @SerializedName("product_id")
    val productId: String,
    val quantity: Int,
    @SerializedName("unit_price")
    val unitPrice: Double = 0.0
)