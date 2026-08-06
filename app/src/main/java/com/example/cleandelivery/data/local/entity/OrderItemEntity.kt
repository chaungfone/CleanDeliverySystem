package com.example.cleandelivery.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.example.cleandelivery.data.model.OrderItemDto

@Entity(tableName = "order_items")
data class OrderItemEntity(
    @PrimaryKey val id: String,
    val orderId: String,
    val productId: String,
    val quantity: Int,
    val unitPrice: Double
)

fun OrderItemDto.toOrderItemEntity() = OrderItemEntity(
    id = id,
    orderId = orderId,
    productId = productId,
    quantity = quantity,
    unitPrice = unitPrice
)

fun OrderItemEntity.toOrderItemDto() = OrderItemDto(
    id = id,
    orderId = orderId,
    productId = productId,
    quantity = quantity,
    unitPrice = unitPrice
)
