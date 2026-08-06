package com.example.cleandelivery.data.remote

import com.example.cleandelivery.data.preference.TokenManager
import okhttp3.Interceptor
import okhttp3.Response
import javax.inject.Inject

/**
 * Attaches the stored JWT to every authenticated request.
 */
class AuthInterceptor @Inject constructor(
    private val tokenManager: TokenManager
) : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val token = tokenManager.getToken()

        val request = chain.request()
        val builder = request.newBuilder().header("Content-Type", "application/json")

        if (!token.isNullOrEmpty()) {
            builder.header("Authorization", "Bearer $token")
        }

        return chain.proceed(builder.build())
    }
}
