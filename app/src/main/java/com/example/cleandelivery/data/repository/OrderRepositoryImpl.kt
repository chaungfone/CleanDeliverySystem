package com.example.cleandelivery.data.repository

import com.example.cleandelivery.data.local.dao.OrderDao
import com.example.cleandelivery.data.local.entity.toOrderItemDto
import com.example.cleandelivery.data.local.entity.toOrderItemEntity
import com.example.cleandelivery.data.local.entity.toOrderEntity
import com.example.cleandelivery.data.model.OrderCreateRequest
import com.example.cleandelivery.data.model.OrderDto
import com.example.cleandelivery.data.remote.ApiService
import com.example.cleandelivery.domain.repository.OrderRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject

class OrderRepositoryImpl @Inject constructor(
    private val api: ApiService,
    private val orderDao: OrderDao
) : OrderRepository {

    override suspend fun createOrder(request: OrderCreateRequest): Result<OrderDto> =
        safeApiCall { api.createOrder(request) }

    override fun getOrderHistory(): Flow<List<OrderDto>> {
        return orderDao.getOrders().map { entities ->
            entities.map { entity ->
                val items = orderDao.getItemsForOrder(entity.id).map { it.toOrderItemDto() }
                OrderDto(
                    id = entity.id,
                    customerId = entity.customerId,
                    driverId = entity.driverId,
                    addressId = entity.addressId,
                    status = entity.status,
                    totalAmount = entity.totalAmount,
                    paymentStatus = entity.paymentStatus,
                    paymentMethod = entity.paymentMethod,
                    emptyBottlesReturned = entity.emptyBottlesReturned,
                    createdAt = entity.createdAt,
                    items = items
                )
            }
        }
    }

    override suspend fun refreshOrderHistory(): Result<Unit> {
        val result = safeApiCall { api.getOrderHistory() }
        return if (result.isSuccess) {
            val orders = result.getOrNull() ?: emptyList()
            val orderEntities = orders.map { it.toOrderEntity() }
            val itemEntities = orders.flatMap { order ->
                order.items.map { it.toOrderItemEntity() }
            }
            orderDao.upsertOrders(orderEntities)
            orderDao.upsertOrderItems(itemEntities)
            Result.success(Unit)
        } else {
            Result.failure(result.exceptionOrNull() ?: Exception("Unknown error"))
        }
    }
}
