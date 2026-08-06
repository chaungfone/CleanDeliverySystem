package com.example.cleandelivery.data.repository

import com.example.cleandelivery.data.model.DriverLocationRequest
import com.example.cleandelivery.data.model.DriverStatusUpdateRequest
import com.example.cleandelivery.data.model.OrderDto
import com.example.cleandelivery.data.remote.ApiService
import com.example.cleandelivery.domain.repository.DriverRepository
import javax.inject.Inject

class DriverRepositoryImpl @Inject constructor(
    private val api: ApiService
) : DriverRepository {

    override suspend fun getAssignedOrders(): Result<List<OrderDto>> =
        safeApiCall { api.getAssignedOrders() }

    override suspend fun updateOrderStatus(orderId: String, status: String): Result<OrderDto> =
        safeApiCall {
            api.updateOrderStatus(orderId, DriverStatusUpdateRequest(status))
        }

    override suspend fun updateLocation(latitude: Double, longitude: Double): Result<Unit> {
        val result = safeApiCall {
            api.updateDriverLocation(DriverLocationRequest(latitude, longitude))
        }
        return if (result.isSuccess) Result.success(Unit) else Result.failure(result.exceptionOrNull()!!)
    }

    override suspend fun getOptimizedRoute(lat: Double, lng: Double): Result<List<Map<String, Any>>> =
        safeApiCall { api.getOptimizedRoute(lat, lng) }
}
