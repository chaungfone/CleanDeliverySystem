package com.example.cleandelivery.data.model

import com.google.gson.annotations.SerializedName

/**
 * Maps the backend `app/models/user.py::UserResponse`.
 *
 * `role` is one of: CUSTOMER | DRIVER | ADMIN.
 */
data class UserResponse(
    val id: String,
    @SerializedName("phone_number")
    val phoneNumber: String,
    @SerializedName("full_name")
    val fullName: String,
    val role: String,
    @SerializedName("created_at")
    val createdAt: String
)