from django.contrib import admin
from .models import TradingPair, Order, Wallet

@admin.register(TradingPair)
class TradingPairAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'base_currency', 'quote_currency', 'is_active', 'created_at']
    list_filter = ['is_active', 'base_currency', 'quote_currency']
    search_fields = ['symbol', 'base_currency', 'quote_currency']
    readonly_fields = ['created_at']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'pair', 'side', 'order_type', 'price', 'amount', 'status', 'created_at']
    list_filter = ['side', 'order_type', 'status', 'pair', 'created_at']
    search_fields = ['user__username', 'pair__symbol']
    readonly_fields = ['created_at', 'updated_at', 'filled_amount']
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'pair')

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'currency', 'balance', 'locked_balance', 'available_balance', 'created_at']
    list_filter = ['currency', 'created_at']
    search_fields = ['user__username', 'currency']
    readonly_fields = ['created_at', 'available_balance']
    
    def available_balance(self, obj):
        return obj.available_balance
    available_balance.short_description = 'Available'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')