package com.example.cleandelivery.domain.repository

import com.example.cleandelivery.data.model.ProductDto
import kotlinx.coroutines.flow.Flow

interface ProductRepository {
    fun getProducts(): Flow<List<ProductDto>>
    suspend fun refreshProducts(): Result<Unit>
}
