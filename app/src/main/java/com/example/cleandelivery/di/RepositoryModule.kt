package com.example.cleandelivery.di

import com.example.cleandelivery.data.repository.AuthRepositoryImpl
import com.example.cleandelivery.data.repository.DriverRepositoryImpl
import com.example.cleandelivery.data.repository.OrderRepositoryImpl
import com.example.cleandelivery.data.repository.ProductRepositoryImpl
import com.example.cleandelivery.domain.repository.AuthRepository
import com.example.cleandelivery.domain.repository.DriverRepository
import com.example.cleandelivery.domain.repository.OrderRepository
import com.example.cleandelivery.domain.repository.ProductRepository
import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {

    @Binds
    @Singleton
    abstract fun bindAuthRepository(
        authRepositoryImpl: AuthRepositoryImpl
    ): AuthRepository

    @Binds
    @Singleton
    abstract fun bindOrderRepository(
        orderRepositoryImpl: OrderRepositoryImpl
    ): OrderRepository

    @Binds
    @Singleton
    abstract fun bindProductRepository(
        productRepositoryImpl: ProductRepositoryImpl
    ): ProductRepository

    @Binds
    @Singleton
    abstract fun bindDriverRepository(
        driverRepositoryImpl: DriverRepositoryImpl
    ): DriverRepository
}
