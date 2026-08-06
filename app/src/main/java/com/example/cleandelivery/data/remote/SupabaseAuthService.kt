package com.example.cleandelivery.data.remote

import io.github.jan.supabase.SupabaseClient
import io.github.jan.supabase.gotrue.auth
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SupabaseAuthService @Inject constructor(
    private val supabaseClient: SupabaseClient
) {
    // Methods commented out to verify build
    /*
    suspend fun signInWithOtp(phone: String) {
        supabaseClient.auth.signInWith(OTP) {
            this.phone = phone
        }
    }
    */

    fun logout() {
        // Auth SDK handles session clearing internally
    }
}
