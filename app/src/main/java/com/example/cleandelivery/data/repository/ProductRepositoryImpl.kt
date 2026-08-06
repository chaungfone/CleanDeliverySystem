package com.example.cleandelivery.data.repository

import com.example.cleandelivery.data.local.dao.ProductDao
import com.example.cleandelivery.data.local.entity.toProductDto
import com.example.cleandelivery.data.local.entity.toProductEntity
import com.example.cleandelivery.data.model.ProductDto
import com.example.cleandelivery.data.remote.ApiService
import com.example.cleandelivery.domain.repository.ProductRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject

class ProductRepositoryImpl @Inject constructor(
    private val api: ApiService,
    private val productDao: ProductDao
) : ProductRepository {

    override fun getProducts(): Flow<List<ProductDto>> {
        return productDao.getProducts().map { entities ->
            entities.map { it.toProductDto() }
        }
    }

    override suspend fun refreshProducts(): Result<Unit> {
        val result = safeApiCall { api.getProducts() }
        return if (result.isSuccess) {
            val products = result.getOrNull() ?: emptyList()
            productDao.upsertProducts(products.map { it.toProductEntity() })
            Result.success(Unit)
        } else {
            Result.failure(result.exceptionOrNull() ?: Exception("Unknown error"))
        }
    }
}
