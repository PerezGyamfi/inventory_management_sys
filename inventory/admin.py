from django.contrib import admin
from .models import Product, Category, StockMovement
from .models import Product, StockHistory


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'quantity', 'price')
    search_fields = ('name',)
    list_filter = ('category',)
    ordering = ('name',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ('name',)


# @admin.register(StockMovement)
# class StockMovementAdmin(admin.ModelAdmin):
#     list_display = ('product', 'movement_type', 'quantity', 'date')
#     list_filter = ('movement_type', 'date')
#     ordering = ('-date',)



@admin.register(StockHistory)
class StockHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'product',
        'action',
        'quantity',
        'user',
        'timestamp',
    )

    list_filter = (
        'action',
        'timestamp',
        'product',
        'user',
    )

    search_fields = (
        'product__name',
        'user__username',
    )

    ordering = ('-timestamp',)

    readonly_fields = (
        'product',
        'action',
        'quantity',
        'user',
        'timestamp',
    )



