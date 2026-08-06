package com.example.cleandelivery.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import com.example.cleandelivery.data.local.dao.OrderDao
import com.example.cleandelivery.data.local.dao.ProductDao
import com.example.cleandelivery.data.local.entity.OrderEntity
import com.example.cleandelivery.data.local.entity.OrderItemEntity
import com.example.cleandelivery.data.local.entity.ProductEntity

@Database(
    entities = [
        ProductEntity::class,
        OrderEntity::class,
        OrderItemEntity::class
    ],
    version = 1,
    exportSchema = false
)
abstract class CleanDeliveryDatabase : RoomDatabase() {
    abstract fun productDao(): ProductDao
    abstract fun orderDao(): OrderDao
}
