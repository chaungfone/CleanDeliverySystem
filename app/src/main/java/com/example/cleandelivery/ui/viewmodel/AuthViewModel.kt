package com.example.cleandelivery.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.cleandelivery.domain.repository.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class AuthViewModel @Inject constructor(
    private val repository: AuthRepository
) : ViewModel() {

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading

    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error

    private val _isOtpSent = MutableStateFlow(false)
    val isOtpSent: StateFlow<Boolean> = _isOtpSent

    private val _isLoggedIn = MutableStateFlow(repository.isLoggedIn())
    val isLoggedIn: StateFlow<Boolean> = _isLoggedIn

    fun requestOtp(phone: String, fullName: String?) {
        viewModelScope.launch {
            _isLoading.value = true
            _error.value = null
            val result = repository.requestOtp(phone, fullName)
            _isLoading.value = false
            if (result.isSuccess) {
                _isOtpSent.value = true
            } else {
                _error.value = result.exceptionOrNull()?.message ?: "Failed to send OTP"
            }
        }
    }

    fun verifyOtp(phone: String, otp: String) {
        viewModelScope.launch {
            _isLoading.value = true
            _error.value = null
            val result = repository.verifyOtp(phone, otp)
            _isLoading.value = false
            if (result.isSuccess) {
                _isLoggedIn.value = true
            } else {
                _error.value = result.exceptionOrNull()?.message ?: "Invalid OTP"
            }
        }
    }
}
