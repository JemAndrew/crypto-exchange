"""
Trading services - business logic for wallets, orders, and matching.
"""

import logging
from decimal import Decimal
from typing import List, Optional, Tuple

from django.db import transaction
from django.db.models import F
from django.contrib.auth.models import User

from .models import Order, TradingPair, Wallet

logger = logging.getLogger(__name__)


class InsufficientBalanceError(Exception):
    def __init__(self, required: Decimal, available: Decimal, currency: str):
        self.required = required
        self.available = available
        self.currency = currency
        super().__init__(
            f"Insufficient {currency}: need {required}, have {available}"
        )


class InvalidOrderError(Exception):
    pass


class WalletNotFoundError(Exception):
    def __init__(self, user_id: int, currency: str):
        super().__init__(f"No {currency} wallet for user {user_id}")


class WalletService:
    """Handles wallet operations - deposits, withdrawals, balance locking."""

    def get_or_create_wallet(self, user: User, currency: str) -> Wallet:
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            currency=currency.upper(),
            defaults={'balance': Decimal('0'), 'locked_balance': Decimal('0')}
        )
        return wallet

    def get_wallet(self, user: User, currency: str) -> Wallet:
        try:
            return Wallet.objects.get(user=user, currency=currency.upper())
        except Wallet.DoesNotExist:
            raise WalletNotFoundError(user.id, currency)

    @transaction.atomic
    def deposit(self, user: User, currency: str, amount: Decimal) -> Wallet:
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")

        wallet = self.get_or_create_wallet(user, currency)

        # F() to avoid race conditions
        Wallet.objects.filter(pk=wallet.pk).update(balance=F('balance') + amount)
        wallet.refresh_from_db()

        logger.info(f"Deposit: {amount} {currency} to user {user.id}")
        return wallet

    @transaction.atomic
    def withdraw(self, user: User, currency: str, amount: Decimal) -> Wallet:
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")

        wallet = Wallet.objects.select_for_update().get(
            user=user, currency=currency.upper()
        )

        if wallet.available_balance < amount:
            raise InsufficientBalanceError(amount, wallet.available_balance, currency)

        wallet.balance -= amount
        wallet.save()

        logger.info(f"Withdrawal: {amount} {currency} from user {user.id}")
        return wallet

    @transaction.atomic
    def lock_balance(self, user: User, currency: str, amount: Decimal) -> Wallet:
        """Lock balance for a pending order."""
        if amount <= 0:
            raise ValueError("Lock amount must be positive")

        wallet = Wallet.objects.select_for_update().get(
            user=user, currency=currency.upper()
        )

        if wallet.available_balance < amount:
            raise InsufficientBalanceError(amount, wallet.available_balance, currency)

        wallet.locked_balance += amount
        wallet.save()
        return wallet

    @transaction.atomic
    def unlock_balance(self, user: User, currency: str, amount: Decimal) -> Wallet:
        """Unlock balance when order is cancelled."""
        if amount <= 0:
            raise ValueError("Unlock amount must be positive")

        wallet = Wallet.objects.select_for_update().get(
            user=user, currency=currency.upper()
        )

        if wallet.locked_balance < amount:
            raise ValueError(f"Can't unlock {amount}: only {wallet.locked_balance} locked")

        wallet.locked_balance -= amount
        wallet.save()
        return wallet

    @transaction.atomic
    def transfer_locked(
        self,
        from_user: User,
        to_user: User,
        currency: str,
        amount: Decimal
    ) -> Tuple[Wallet, Wallet]:
        """Transfer from locked balance to another user's available balance."""
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")

        from_wallet = Wallet.objects.select_for_update().get(
            user=from_user, currency=currency.upper()
        )

        if from_wallet.locked_balance < amount:
            raise ValueError(f"Can't transfer {amount}: only {from_wallet.locked_balance} locked")

        from_wallet.locked_balance -= amount
        from_wallet.balance -= amount
        from_wallet.save()

        to_wallet = self.get_or_create_wallet(to_user, currency)
        to_wallet = Wallet.objects.select_for_update().get(pk=to_wallet.pk)
        to_wallet.balance += amount
        to_wallet.save()

        return from_wallet, to_wallet


class OrderValidationService:
    """Validates orders before placement."""

    MIN_ORDER_VALUE = Decimal('10.00')
    MAX_ORDER_VALUE = Decimal('1000000.00')

    def __init__(self):
        self.wallet_svc = WalletService()

    def validate(
        self,
        user: User,
        pair: TradingPair,
        side: str,
        order_type: str,
        price: Decimal,
        amount: Decimal
    ):
        if not pair.is_active:
            raise InvalidOrderError(f"Pair {pair.symbol} is inactive")

        if side not in ('BUY', 'SELL'):
            raise InvalidOrderError(f"Invalid side: {side}")

        if order_type not in ('LIMIT', 'MARKET'):
            raise InvalidOrderError(f"Invalid type: {order_type}")

        if order_type == 'LIMIT' and price <= 0:
            raise InvalidOrderError("Price must be positive")

        if amount <= 0:
            raise InvalidOrderError("Amount must be positive")

        order_value = price * amount
        if order_value < self.MIN_ORDER_VALUE:
            raise InvalidOrderError(f"Min order value is {self.MIN_ORDER_VALUE}")
        if order_value > self.MAX_ORDER_VALUE:
            raise InvalidOrderError(f"Max order value is {self.MAX_ORDER_VALUE}")

        # Check balance
        if side == 'BUY':
            required = price * amount
            currency = pair.quote_currency
        else:
            required = amount
            currency = pair.base_currency

        try:
            wallet = self.wallet_svc.get_wallet(user, currency)
            available = wallet.available_balance
        except WalletNotFoundError:
            available = Decimal('0')

        if available < required:
            raise InsufficientBalanceError(required, available, currency)


class OrderMatchingService:
    """
    Matches orders using price-time priority.

    For BUY orders: match with lowest SELL price first
    For SELL orders: match with highest BUY price first
    """

    def __init__(self):
        self.wallet_svc = WalletService()

    def find_matches(self, order: Order) -> List[Order]:
        opposite = 'SELL' if order.side == 'BUY' else 'BUY'

        matches = Order.objects.filter(
            pair=order.pair,
            side=opposite,
            status='OPEN'
        ).select_for_update()

        if order.side == 'BUY':
            # Match with sells at or below our price
            matches = matches.filter(price__lte=order.price).order_by('price', 'created_at')
        else:
            # Match with buys at or above our price
            matches = matches.filter(price__gte=order.price).order_by('-price', 'created_at')

        return list(matches)

    @transaction.atomic
    def execute_match(self, taker: Order, maker: Order, qty: Decimal):
        """Execute a match between taker and maker orders."""
        price = maker.price
        value = price * qty

        if taker.side == 'BUY':
            buyer, seller = taker.user, maker.user
        else:
            buyer, seller = maker.user, taker.user

        # Transfer base currency (BTC etc) from seller to buyer
        self.wallet_svc.transfer_locked(
            seller, buyer, taker.pair.base_currency, qty
        )

        # Transfer quote currency (GBP etc) from buyer to seller
        self.wallet_svc.transfer_locked(
            buyer, seller, taker.pair.quote_currency, value
        )

        # Update filled amounts
        taker.filled_amount += qty
        maker.filled_amount += qty

        if taker.filled_amount >= taker.amount:
            taker.status = 'FILLED'
        if maker.filled_amount >= maker.amount:
            maker.status = 'FILLED'

        taker.save()
        maker.save()

        logger.info(
            f"Trade: {qty} {taker.pair.base_currency} @ {price} "
            f"(orders {taker.id}/{maker.id})"
        )

    @transaction.atomic
    def match_order(self, order: Order) -> int:
        """Try to match order against the book. Returns number of trades."""
        matches = self.find_matches(order)
        trades = 0

        for maker in matches:
            taker_remaining = order.amount - order.filled_amount
            maker_remaining = maker.amount - maker.filled_amount

            if taker_remaining <= 0:
                break

            qty = min(taker_remaining, maker_remaining)
            self.execute_match(order, maker, qty)
            trades += 1

        return trades


class OrderService:
    """Main entry point for order operations."""

    def __init__(self):
        self.wallet_svc = WalletService()
        self.validator = OrderValidationService()
        self.matcher = OrderMatchingService()

    @transaction.atomic
    def place_order(
        self,
        user: User,
        pair: TradingPair,
        side: str,
        order_type: str,
        price: Decimal,
        amount: Decimal
    ) -> Order:
        # Validate
        self.validator.validate(user, pair, side, order_type, price, amount)

        # Lock balance
        if side == 'BUY':
            self.wallet_svc.lock_balance(user, pair.quote_currency, price * amount)
        else:
            self.wallet_svc.lock_balance(user, pair.base_currency, amount)

        # Create order
        order = Order.objects.create(
            user=user,
            pair=pair,
            side=side,
            order_type=order_type,
            price=price,
            amount=amount,
            status='OPEN'
        )

        logger.info(f"Order {order.id}: {side} {amount} {pair.symbol} @ {price}")

        # Try to match
        trades = self.matcher.match_order(order)
        if trades:
            order.refresh_from_db()

        return order

    @transaction.atomic
    def cancel_order(self, user: User, order_id: int) -> Order:
        order = Order.objects.select_for_update().get(id=order_id)

        if order.user_id != user.id:
            raise InvalidOrderError("Not your order")

        if order.status not in ('PENDING', 'OPEN'):
            raise InvalidOrderError(f"Can't cancel {order.status} order")

        unfilled = order.amount - order.filled_amount

        if unfilled > 0:
            if order.side == 'BUY':
                self.wallet_svc.unlock_balance(
                    user, order.pair.quote_currency, order.price * unfilled
                )
            else:
                self.wallet_svc.unlock_balance(
                    user, order.pair.base_currency, unfilled
                )

        order.status = 'CANCELLED'
        order.save()

        logger.info(f"Order {order.id} cancelled")
        return order

    def get_user_orders(
        self,
        user: User,
        status: Optional[str] = None,
        pair: Optional[TradingPair] = None
    ) -> List[Order]:
        qs = Order.objects.filter(user=user)
        if status:
            qs = qs.filter(status=status)
        if pair:
            qs = qs.filter(pair=pair)
        return qs.order_by('-created_at')

    def get_order_book(self, pair: TradingPair, side: Optional[str] = None) -> List[Order]:
        qs = Order.objects.filter(pair=pair, status='OPEN')
        if side:
            qs = qs.filter(side=side)

        if side == 'BUY':
            return list(qs.order_by('-price', 'created_at'))
        return list(qs.order_by('price', 'created_at'))
