package com.example.cleandelivery.data.remote

import io.github.jan.supabase.SupabaseClient
import io.github.jan.supabase.realtime.Realtime
import io.github.jan.supabase.realtime.realtime
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class RealtimeService @Inject constructor(
    private val supabaseClient: SupabaseClient
) {
    fun getRealtime(): Realtime = supabaseClient.realtime
}
