package com.example.cleandelivery.domain.repository

import com.example.cleandelivery.data.model.OrderCreateRequest
import com.example.cleandelivery.data.model.OrderDto
import kotlinx.coroutines.flow.Flow

interface OrderRepository {
    suspend fun createOrder(request: OrderCreateRequest): Result<OrderDto>
    fun getOrderHistory(): Flow<List<OrderDto>>
    suspend fun refreshOrderHistory(): Result<Unit>
}
