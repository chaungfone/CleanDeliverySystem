package com.example.cleandelivery.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.cleandelivery.data.model.OrderCreateRequest
import com.example.cleandelivery.data.model.OrderDto
import com.example.cleandelivery.domain.repository.OrderRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class OrderViewModel @Inject constructor(
    private val repository: OrderRepository
) : ViewModel() {

    val orders: StateFlow<List<OrderDto>> = repository.getOrderHistory()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading

    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error

    fun placeOrder(request: OrderCreateRequest) {
        viewModelScope.launch {
            _isLoading.value = true
            _error.value = null
            val result = repository.createOrder(request)
            _isLoading.value = false
            if (result.isFailure) {
                _error.value = result.exceptionOrNull()?.message ?: "Failed to place order"
            }
        }
    }

    fun refreshOrderHistory() {
        viewModelScope.launch {
            _isLoading.value = true
            _error.value = null
            val result = repository.refreshOrderHistory()
            _isLoading.value = false
            if (result.isFailure) {
                _error.value = result.exceptionOrNull()?.message ?: "Failed to load orders"
            }
        }
    }
}
