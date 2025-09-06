from django.db import models
from django.contrib.auth.models import user

# Create your models here.
class Order(models.Model): 
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pair = models.CharField(max_length=20, default='BTC/USDT')
    side = models.CharField(max_length=4)  # BUY or SELL
    price = models.DecimalField(max_digits=20, decimal_places=2)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): 
        return f"{self.side} {self.amount} @ {self.price}"