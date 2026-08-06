package com.example.cleandelivery.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.example.cleandelivery.data.model.OrderDto

enum class SyncStatus {
    SYNCED, PENDING
}

@Entity(tableName = "orders")
data class OrderEntity(
    @PrimaryKey val id: String,
    val customerId: String,
    val driverId: String?,
    val addressId: String,
    val status: String,
    val totalAmount: Double,
    val paymentStatus: String,
    val paymentMethod: String,
    val emptyBottlesReturned: Int,
    val createdAt: String,
    val syncStatus: SyncStatus = SyncStatus.SYNCED
)

fun OrderDto.toOrderEntity(syncStatus: SyncStatus = SyncStatus.SYNCED) = OrderEntity(
    id = id,
    customerId = customerId,
    driverId = driverId,
    addressId = addressId,
    status = status,
    totalAmount = totalAmount,
    paymentStatus = paymentStatus,
    paymentMethod = paymentMethod,
    emptyBottlesReturned = emptyBottlesReturned,
    createdAt = createdAt,
    syncStatus = syncStatus
)
