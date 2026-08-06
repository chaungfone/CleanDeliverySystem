package com.example.cleandelivery.di

import android.content.Context
import androidx.room.Room
import com.example.cleandelivery.data.local.CleanDeliveryDatabase
import com.example.cleandelivery.data.local.dao.OrderDao
import com.example.cleandelivery.data.local.dao.ProductDao
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): CleanDeliveryDatabase {
        return Room.databaseBuilder(
            context,
            CleanDeliveryDatabase::class.java,
            "clean_delivery_db"
        ).build()
    }

    @Provides
    fun provideProductDao(db: CleanDeliveryDatabase): ProductDao = db.productDao()

    @Provides
    fun provideOrderDao(db: CleanDeliveryDatabase): OrderDao = db.orderDao()
}
