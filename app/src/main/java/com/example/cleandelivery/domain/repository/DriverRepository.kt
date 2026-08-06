package com.example.cleandelivery.domain.repository

import com.example.cleandelivery.data.model.OrderDto

interface DriverRepository {
    suspend fun getAssignedOrders(): Result<List<OrderDto>>
    suspend fun updateOrderStatus(orderId: String, status: String): Result<OrderDto>
    suspend fun updateLocation(latitude: Double, longitude: Double): Result<Unit>
    suspend fun getOptimizedRoute(lat: Double, lng: Double): Result<List<Map<String, Any>>>
}
