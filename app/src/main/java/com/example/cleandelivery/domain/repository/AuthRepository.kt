package com.example.cleandelivery.domain.repository

import com.example.cleandelivery.data.model.AuthResponse
import com.example.cleandelivery.data.model.RequestOtpResponse
import com.example.cleandelivery.data.model.UserResponse

interface AuthRepository {
    suspend fun requestOtp(phoneNumber: String, fullName: String? = null): Result<RequestOtpResponse>
    suspend fun verifyOtp(phoneNumber: String, otp: String): Result<AuthResponse>
    suspend fun getCurrentUser(): Result<UserResponse>
    fun isLoggedIn(): Boolean
    fun logout()
}
