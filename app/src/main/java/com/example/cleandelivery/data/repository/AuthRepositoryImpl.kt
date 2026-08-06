package com.example.cleandelivery.data.repository

import com.example.cleandelivery.data.model.AuthResponse
import com.example.cleandelivery.data.model.RequestOtpRequest
import com.example.cleandelivery.data.model.RequestOtpResponse
import com.example.cleandelivery.data.model.UserResponse
import com.example.cleandelivery.data.model.VerifyOtpRequest
import com.example.cleandelivery.data.preference.TokenManager
import com.example.cleandelivery.data.remote.ApiService
import com.example.cleandelivery.domain.repository.AuthRepository
import javax.inject.Inject

class AuthRepositoryImpl @Inject constructor(
    private val api: ApiService,
    private val tokenManager: TokenManager
) : AuthRepository {

    override suspend fun requestOtp(phoneNumber: String, fullName: String?): Result<RequestOtpResponse> =
        safeApiCall {
            api.requestOtp(RequestOtpRequest(phoneNumber = phoneNumber, fullName = fullName))
        }

    override suspend fun verifyOtp(phoneNumber: String, otp: String): Result<AuthResponse> =
        safeApiCall {
            api.verifyOtp(VerifyOtpRequest(phoneNumber = phoneNumber, otp = otp))
        }.onSuccess { auth ->
            tokenManager.saveTokens(auth.accessToken, auth.refreshToken)
        }

    override suspend fun getCurrentUser(): Result<UserResponse> =
        safeApiCall { api.getCurrentUser() }

    override fun isLoggedIn(): Boolean = tokenManager.isLoggedIn()

    override fun logout() = tokenManager.clear()
}
