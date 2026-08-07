package com.example.cleandelivery.data.remote

import com.example.cleandelivery.data.preference.TokenManager
import com.google.gson.Gson
import okhttp3.Authenticator
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import okhttp3.Route
import javax.inject.Inject

/**
 * OkHttp Authenticator that attempts to refresh tokens when a 401 is received.
 * It performs a synchronous POST /auth/refresh with the stored refresh token and
 * updates TokenManager with the rotated tokens.
 */
class TokenAuthenticator @Inject constructor(
    private val tokenManager: TokenManager
) : Authenticator {

    private val BASE_URL = "http://10.0.2.2:8000/api/v1/"

    override fun authenticate(route: Route?, response: Response): Request? {
        // synchronized to ensure only one refresh happens at a time
        synchronized(this) {
            // If we've already attempted to authenticate with a fresh token, give up
            val priorRequestToken = response.request.header("Authorization")?.removePrefix("Bearer ")
            val currentToken = tokenManager.getToken()
            if (!priorRequestToken.isNullOrEmpty() && !currentToken.isNullOrEmpty() && priorRequestToken != currentToken) {
                // Another thread refreshed the token; retry with current token
                return response.request.newBuilder()
                    .header("Authorization", "Bearer $currentToken")
                    .build()
            }

            val refreshToken = tokenManager.getRefreshToken() ?: return null

            // Perform a synchronous refresh call using a fresh OkHttpClient to avoid interceptor loops
            val client = OkHttpClient.Builder().build()
            val mediaType = "application/json; charset=utf-8".toMediaType()
            val safeRefresh = refreshToken.replace("\"", "\\\"")
            val body = ("{\"refresh_token\":\"" + safeRefresh + "\"}").toRequestBody(mediaType)
            val req = Request.Builder()
                .url(BASE_URL + "auth/refresh")
                .post(body)
                .addHeader("X-Client-Type", "mobile")
                .addHeader("Content-Type", "application/json")
                .build()

            val resp = try {
                client.newCall(req).execute()
            } catch (e: Exception) {
                tokenManager.clear()
                return null
            }

            if (!resp.isSuccessful) {
                tokenManager.clear()
                return null
            }

            val respBody = resp.body?.string() ?: run {
                tokenManager.clear()
                return null
            }

            val gson = Gson()
            val map: Map<*, *> = try {
                gson.fromJson(respBody, Map::class.java)
            } catch (e: Exception) {
                tokenManager.clear()
                return null
            }

            val newAccess = map["access_token"] as? String
            val newRefresh = map["refresh_token"] as? String

            if (newAccess.isNullOrEmpty() || newRefresh.isNullOrEmpty()) {
                tokenManager.clear()
                return null
            }

            // Persist rotated tokens
            tokenManager.saveTokens(newAccess, newRefresh)

            // Retry the failed request with the new access token
            return response.request.newBuilder()
                .header("Authorization", "Bearer $newAccess")
                .build()
        }
    }
}
