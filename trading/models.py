from django.db import models
from django.contrib.auth.models import User  # Fixed: Capital U
from decimal import Decimal

class TradingPair(models.Model):
    symbol = models.CharField(max_length=20, unique=True)  # e.g., "BTC/USDT"
    base_currency = models.CharField(max_length=10)  # BTC
    quote_currency = models.CharField(max_length=10)  # USDT
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.symbol

class Order(models.Model):
    ORDER_TYPES = [
        ('LIMIT', 'Limit'),
        ('MARKET', 'Market'),
    ]
    
    ORDER_SIDES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]
    
    ORDER_STATUS = [
        ('PENDING', 'Pending'),
        ('OPEN', 'Open'),
        ('FILLED', 'Filled'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    pair = models.ForeignKey(TradingPair, on_delete=models.CASCADE)
    side = models.CharField(max_length=4, choices=ORDER_SIDES)
    order_type = models.CharField(max_length=10, choices=ORDER_TYPES, default='LIMIT')
    price = models.DecimalField(max_digits=20, decimal_places=2)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    filled_amount = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0'))
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['pair', 'status']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self): 
        return f"{self.side} {self.amount} {self.pair.symbol} @ {self.price}"

class Wallet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallets')
    currency = models.CharField(max_length=10)  # BTC, USDT, GBP, etc.
    balance = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0'))
    locked_balance = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'currency']

    @property
    def available_balance(self):
        return self.balance - self.locked_balance

    def __str__(self):
        return f"{self.user.username} - {self.currency}: {self.balance}"