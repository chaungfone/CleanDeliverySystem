package com.example.cleandelivery.data.repository

import retrofit2.Response
import java.io.IOException

/**
 * Executes a Retrofit suspend call and unwraps the [Response], returning a
 * [Result] that models success/failure with a human-readable error message.
 */
internal suspend fun <T> safeApiCall(block: suspend () -> Response<T>): Result<T> {
    return try {
        val response = block()
        if (response.isSuccessful) {
            val body = response.body()
            if (body != null) {
                Result.success(body)
            } else {
                Result.failure(IOException("Empty response body"))
            }
        } else {
            Result.failure(IOException("Request failed (${response.code()}): ${response.errorBody()?.string()}"))
        }
    } catch (e: Exception) {
        Result.failure(e)
    }
}