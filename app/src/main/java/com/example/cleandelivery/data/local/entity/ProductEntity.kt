package com.example.cleandelivery.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.example.cleandelivery.data.model.ProductDto

@Entity(tableName = "products")
data class ProductEntity(
    @PrimaryKey val id: String,
    val name: String,
    val description: String?,
    val price: Double,
    val depositFee: Double,
    val stockQuantity: Int,
    val createdAt: String
)

fun ProductDto.toProductEntity() = ProductEntity(
    id = id,
    name = name,
    description = description,
    price = price,
    depositFee = depositFee,
    stockQuantity = stockQuantity,
    createdAt = createdAt
)

fun ProductEntity.toProductDto() = ProductDto(
    id = id,
    name = name,
    description = description,
    price = price,
    depositFee = depositFee,
    stockQuantity = stockQuantity,
    createdAt = createdAt
)
