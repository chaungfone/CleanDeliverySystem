package com.example.cleandelivery.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.cleandelivery.data.model.OrderDto
import com.example.cleandelivery.domain.repository.DriverRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class DriverViewModel @Inject constructor(
    private val repository: DriverRepository
) : ViewModel() {

    private val _isOnline = MutableStateFlow(false)
    val isOnline: StateFlow<Boolean> = _isOnline

    private val _assignedOrders = MutableStateFlow<List<OrderDto>>(emptyList())
    val assignedOrders: StateFlow<List<OrderDto>> = _assignedOrders

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading

    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error

    fun toggleOnlineStatus() {
        _isOnline.value = !_isOnline.value
        // In production, update status via API
    }

    fun fetchAssignedOrders() {
        viewModelScope.launch {
            _isLoading.value = true
            val result = repository.getAssignedOrders()
            _isLoading.value = false
            if (result.isSuccess) {
                _assignedOrders.value = result.getOrNull() ?: emptyList()
            } else {
                _error.value = result.exceptionOrNull()?.message ?: "Failed to fetch orders"
            }
        }
    }

    fun updateOrderStatus(orderId: String, status: String) {
        viewModelScope.launch {
            _isLoading.value = true
            val result = repository.updateOrderStatus(orderId, status)
            _isLoading.value = false
            if (result.isSuccess) {
                fetchAssignedOrders() // Refresh list
            } else {
                _error.value = result.exceptionOrNull()?.message ?: "Failed to update status"
            }
        }
    }

    fun updateLocation(lat: Double, lng: Double) {
        viewModelScope.launch {
            repository.updateLocation(lat, lng)
        }
    }
}
