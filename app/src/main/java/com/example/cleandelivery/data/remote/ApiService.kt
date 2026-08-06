package com.example.cleandelivery.data.remote

import com.example.cleandelivery.data.model.AdminAnalyticsResponse
import com.example.cleandelivery.data.model.AdminStatsResponse
import com.example.cleandelivery.data.model.AuthResponse
import com.example.cleandelivery.data.model.DriverLocationRequest
import com.example.cleandelivery.data.model.DriverStatusUpdateRequest
import com.example.cleandelivery.data.model.OrderCreateRequest
import com.example.cleandelivery.data.model.OrderDto
import com.example.cleandelivery.data.model.ProductDto
import com.example.cleandelivery.data.model.RequestOtpRequest
import com.example.cleandelivery.data.model.RequestOtpResponse
import com.example.cleandelivery.data.model.UserResponse
import com.example.cleandelivery.data.model.VerifyOtpRequest
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

/**
 * Retrofit contract mirroring the Python FastAPI router in
 * `backend/app/api/v1/router.py`.
 *
 * Base URL is expected to include the `/api/v1` prefix (see RetrofitClient),
 * so all paths below are relative to it.
 */
interface ApiService {

    // ----------------------------- Auth -----------------------------
    @POST("auth/request-otp")
    suspend fun requestOtp(@Body request: RequestOtpRequest): Response<RequestOtpResponse>

    @POST("auth/verify-otp")
    suspend fun verifyOtp(@Body request: VerifyOtpRequest): Response<AuthResponse>

    @GET("auth/me")
    suspend fun getCurrentUser(): Response<UserResponse>

    // ---------------------------- Products ---------------------------
    @GET("products")
    suspend fun getProducts(): Response<List<ProductDto>>

    // ----------------------------- Orders ----------------------------
    @POST("orders")
    suspend fun createOrder(@Body request: OrderCreateRequest): Response<OrderDto>

    @GET("orders/history")
    suspend fun getOrderHistory(): Response<List<OrderDto>>

    // -------------------------- Admin ------------------------
    @GET("admin/dashboard/stats")
    suspend fun getAdminStats(): Response<AdminStatsResponse>

    @GET("admin/dashboard/analytics")
    suspend fun getAdminAnalytics(@Query("period") period: String = "daily"): Response<AdminAnalyticsResponse>

    // -------------------------- Driver ------------------------
    @GET("drivers/orders")
    suspend fun getAssignedOrders(): Response<List<OrderDto>>

    @PATCH("drivers/orders/{order_id}/status")
    suspend fun updateOrderStatus(
        @Path("order_id") orderId: String,
        @Body request: DriverStatusUpdateRequest
    ): Response<OrderDto>

    @POST("drivers/location")
    suspend fun updateDriverLocation(@Body request: DriverLocationRequest): Response<Unit>

    @POST("drivers/optimize-route")
    suspend fun getOptimizedRoute(
        @Query("current_lat") lat: Double,
        @Query("current_lng") lng: Double
    ): Response<List<Map<String, Any>>>
}
