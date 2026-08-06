package com.example.cleandelivery.data.model

import com.google.gson.annotations.SerializedName

/**
 * Maps the backend `app/api/v1/endpoints/auth.py` request/response bodies.
 */

data class RequestOtpRequest(
    @SerializedName("phone_number")
    val phoneNumber: String,
    @SerializedName("full_name")
    val fullName: String? = null
)

data class RequestOtpResponse(
    val message: String,
    @SerializedName("phone_number")
    val phoneNumber: String,
    /** Only present when `settings.DEBUG` is true — useful during development. */
    @SerializedName("debug_otp")
    val debugOtp: String? = null
)

data class VerifyOtpRequest(
    @SerializedName("phone_number")
    val phoneNumber: String,
    val otp: String
)

data class AuthResponse(
    @SerializedName("access_token")
    val accessToken: String,
    @SerializedName("refresh_token")
    val refreshToken: String,
    val role: String,
    @SerializedName("user_id")
    val userId: String
)