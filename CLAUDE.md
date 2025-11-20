# CLAUDE.md - Cryptocurrency Exchange Platform

## Project Vision

We are building a **professional-grade, FCA-compliant cryptocurrency exchange** focused on stablecoins and major cryptocurrencies. Our goal is to provide UK customers with a secure, fast, and user-friendly platform for trading digital assets with proper regulatory oversight.

This is **not a side project or academic exercise** - we're building a real financial services platform that will handle real money and must meet enterprise-grade standards for security, reliability, and compliance.

---

## Core Principles

### 1. Regulatory Compliance First

**We operate in a heavily regulated industry.** Every technical decision must consider:

- FCA registration requirements
- Anti-Money Laundering (AML) regulations
- Know Your Customer (KYC) obligations
- Financial Conduct Authority oversight
- Data protection (GDPR)
- Customer asset protection rules

**Legal reality:**
- Development on testnet: ✅ No licence required
- Internal testing only: ✅ Permitted with proper agreements
- Public beta with real money: ❌ Illegal without FCA authorisation
- Production launch: ✅ Only after FCA approval (12-18 months)

### 2. Security is Non-Negotiable

We are a **custodial exchange** - we hold customer funds. A security breach means:
- Loss of customer money
- Criminal liability
- End of business
- Personal liability for directors

**Security must be:**
- Built in from day one (not added later)
- Reviewed in every code review
- Tested continuously
- Audited by external experts
- Documented comprehensively

### 3. Code Quality Matters

We write code that will:
- Handle millions of pounds
- Process thousands of transactions per second
- Be audited by regulators
- Be reviewed by security experts
- Be maintained for years
- Potentially be used as evidence in legal proceedings

**Poor code quality is not acceptable.**

---

## Development Philosophy

### KISS (Keep It Simple, Stupid)

**Write the simplest code that works.**

```python
# ❌ BAD: Clever but confusing
def process(x): return [i**2 for i in x if i%2==0 and i>0]

# ✅ GOOD: Clear and obvious
def calculate_squares_of_positive_even_numbers(numbers):
    """
    Calculate squares of positive even numbers from input list.
    
    Args:
        numbers: List of integers
        
    Returns:
        List of squared values
    """
    result = []
    for number in numbers:
        if number > 0 and number % 2 == 0:
            result.append(number ** 2)
    return result
```

**Rules:**
- Prefer clarity over cleverness
- If it needs a comment to explain, simplify the code
- Avoid "clever" one-liners
- No complex abstractions unless absolutely necessary
- Variable names should be descriptive, not abbreviated

### YAGNI (You Aren't Gonna Need It)

**Only build features that are explicitly requested.**

```python
# ❌ BAD: Building for future needs
class Order(models.Model):
    # ... basic fields ...
    
    # "Just in case" we need these later:
    metadata = models.JSONField(default=dict)
    extra_data = models.TextField(blank=True)
    future_use_1 = models.CharField(max_length=100, blank=True)
    future_use_2 = models.CharField(max_length=100, blank=True)

# ✅ GOOD: Only what's needed now
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pair = models.ForeignKey(TradingPair, on_delete=models.CASCADE)
    side = models.CharField(max_length=4, choices=ORDER_SIDES)
    price = models.DecimalField(max_digits=20, decimal_places=2)
    quantity = models.DecimalField(max_digits=20, decimal_places=8)
    status = models.CharField(max_length=20, choices=ORDER_STATUS)
    created_at = models.DateTimeField(auto_now_add=True)
```

**Rules:**
- Don't add "just in case" functionality
- Don't build extensibility until needed
- MVP first, then iterate
- Delete unused code immediately
- No speculative features

### SOLID Principles

#### Single Responsibility Principle

**Each class/function does ONE thing.**

```python
# ❌ BAD: Model doing too much
class Order(models.Model):
    # ... fields ...
    
    def execute(self):
        """Execute order, match with others, update balances..."""
        # 200 lines of business logic
        pass

# ✅ GOOD: Separate concerns
class Order(models.Model):
    """Data structure only - represents an order."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pair = models.ForeignKey(TradingPair, on_delete=models.CASCADE)
    # ... other fields only ...

class OrderExecutionService:
    """Business logic for executing orders."""
    
    def execute_order(self, order: Order) -> ExecutionResult:
        """
        Execute an order against the order book.
        
        Single responsibility: order execution logic.
        """
        # Business logic here
        pass
```

**Code organisation:**
```
trading/
├── models.py          # Data structures ONLY
├── services.py        # Business logic ONLY
├── views.py          # Request/response handling ONLY
├── serializers.py    # Data validation/serialisation ONLY
├── forms.py          # Form validation ONLY
└── utils.py          # Pure utility functions ONLY
```

#### Open/Closed Principle

**Easy to extend without modifying existing code.**

```python
# ✅ GOOD: Easy to add new order types
class OrderValidator:
    """Base validator for orders."""
    
    def validate(self, order: Order) -> bool:
        raise NotImplementedError

class LimitOrderValidator(OrderValidator):
    def validate(self, order: Order) -> bool:
        return order.price is not None and order.price > 0

class MarketOrderValidator(OrderValidator):
    def validate(self, order: Order) -> bool:
        return order.quantity > 0

class StopLimitOrderValidator(OrderValidator):
    def validate(self, order: Order) -> bool:
        return (order.price is not None and 
                order.stop_price is not None and
                order.stop_price > 0)

# Adding a new order type? Just add a new validator class.
# No need to modify existing code.
```

#### Liskov Substitution Principle

**Subclasses should work anywhere parent class works.**

```python
# ✅ GOOD: Consistent interface
class BlockchainConnector:
    def get_balance(self, address: str) -> Decimal:
        raise NotImplementedError
    
    def send_transaction(self, to: str, amount: Decimal) -> str:
        raise NotImplementedError

class EthereumConnector(BlockchainConnector):
    def get_balance(self, address: str) -> Decimal:
        return self.w3.eth.get_balance(address)
    
    def send_transaction(self, to: str, amount: Decimal) -> str:
        # Implementation
        pass

class BitcoinConnector(BlockchainConnector):
    def get_balance(self, address: str) -> Decimal:
        # Different implementation, same interface
        pass
    
    def send_transaction(self, to: str, amount: Decimal) -> str:
        # Implementation
        pass

# Can swap implementations without changing client code
def process_withdrawal(connector: BlockchainConnector, address: str, amount: Decimal):
    balance = connector.get_balance(address)  # Works with any connector
    if balance >= amount:
        return connector.send_transaction(address, amount)
```

#### Interface Segregation Principle

**Small, focused interfaces.**

```python
# ❌ BAD: Fat interface
class TradingService:
    def place_order(self): pass
    def cancel_order(self): pass
    def get_order_book(self): pass
    def get_user_orders(self): pass
    def get_trade_history(self): pass
    def calculate_fees(self): pass
    def validate_order(self): pass
    def match_orders(self): pass
    # Too many responsibilities!

# ✅ GOOD: Focused interfaces
class OrderPlacementService:
    """Handles placing orders only."""
    def place_order(self, order: Order) -> ExecutionResult:
        pass

class OrderMatchingService:
    """Handles matching orders only."""
    def match_orders(self, pair: TradingPair) -> List[Trade]:
        pass

class OrderValidationService:
    """Handles order validation only."""
    def validate_order(self, order: Order) -> ValidationResult:
        pass
```

#### Dependency Inversion Principle

**Depend on abstractions, not concrete implementations.**

```python
# ❌ BAD: View directly depends on implementation
class OrderView(APIView):
    def post(self, request):
        # Directly creating and using concrete classes
        engine = MatchingEngine(TradingPair.objects.get(id=1))
        validator = OrderValidator()
        # Tightly coupled to implementations
        pass

# ✅ GOOD: View depends on service abstraction
class OrderView(APIView):
    def __init__(self):
        # Depend on abstractions (can swap implementations)
        self.order_service = OrderService()
        # Could easily swap to MockOrderService for testing
    
    def post(self, request):
        serialiser = OrderSerializer(data=request.data)
        serialiser.is_valid(raise_exception=True)
        
        # Service handles all business logic
        result = self.order_service.place_order(
            user=request.user,
            **serialiser.validated_data
        )
        
        return Response(result)
```

---

## Technical Stack

### Backend
```yaml
Language: Python 3.11+
Framework: Django 5.2+
API: Django REST Framework 3.16+
Real-time: Django Channels 4+ (WebSocket)
Task Queue: Celery 5+ with Redis
Database: PostgreSQL 15+
  - TimescaleDB extension for time-series data
Cache: Redis 7+
Search: Elasticsearch 8+ (optional, for analytics)
```

### Frontend
```yaml
Language: TypeScript 5+
Framework: React 18+
Build Tool: Vite 5+
State Management: Zustand or Redux Toolkit
UI Library: Tailwind CSS 3+ with shadcn/ui
Charts: TradingView Lightweight Charts
Real-time: Socket.io-client or native WebSocket
```

### Blockchain
```yaml
Ethereum: web3.py 6+
Bitcoin: bitcoinlib or python-bitcoinlib
HD Wallets: eth-account with BIP32/BIP39
Node Provider: Infura or Alchemy (production) / testnet (development)
Networks: 
  - Development: Sepolia (Ethereum), Mumbai (Polygon)
  - Production: Ethereum Mainnet, Polygon, BSC
```

### Infrastructure
```yaml
Containerisation: Docker 24+ with Docker Compose
Orchestration: Kubernetes (production)
Web Server: Nginx 1.24+
WSGI Server: Gunicorn 21+
Load Balancer: Nginx or AWS ALB
CDN: CloudFlare
Monitoring: Grafana + Prometheus
Logging: ELK Stack (Elasticsearch, Logstash, Kibana)
CI/CD: GitHub Actions
```

### Security
```yaml
Authentication: JWT with refresh tokens
2FA: TOTP (Time-based One-Time Password)
Password Hashing: bcrypt (never MD5, SHA1)
Key Storage: AWS KMS or HashiCorp Vault (production)
SSL/TLS: Let's Encrypt certificates
Rate Limiting: Redis-based
DDoS Protection: CloudFlare
Security Headers: django-security, CSP, HSTS
```

### Development Tools
```yaml
Version Control: Git with conventional commits
Code Quality: 
  - Black (Python formatter)
  - Pylint (Python linter)
  - ESLint + Prettier (TypeScript/React)
  - pre-commit hooks
Testing:
  - pytest (backend)
  - Jest (frontend)
  - Coverage requirements: 80%+
Documentation: Swagger/OpenAPI for API docs
```

---

## Architecture Decisions

### Why Centralized Exchange (CEX)?

**We chose a centralized architecture over decentralized (DEX) because:**

1. **Speed**: Instant trades (milliseconds) vs blockchain speed (12+ seconds)
2. **Cost**: Zero trading fees vs £1-50 gas fees per trade
3. **UX**: Email/password login vs crypto wallet complexity
4. **Regulation**: Clear FCA path vs uncertain legal status
5. **Support**: Can help users vs no support possible
6. **Volume**: Unlimited throughput vs blockchain limits

### Why Off-Chain Order Matching?

**Orders are matched in our database, not on blockchain:**

```
Order Placement → PostgreSQL → Matching Engine → Trade Execution
     ↓                                                  ↓
  <100ms                                        Update balances
                                                       ↓
                                              Blockchain only for
                                              deposits/withdrawals
```

**Benefits:**
- **Fast**: Thousands of orders per second
- **Free**: No gas fees for trading
- **Complex**: Support stop-loss, trailing stops, etc.
- **Reliable**: Not affected by blockchain congestion

### Why PostgreSQL Over NoSQL?

**Transactions are critical for financial applications:**

```python
# ACID guarantees are essential
@transaction.atomic
def execute_trade(buy_order, sell_order):
    # Either ALL of these happen, or NONE
    buy_order.filled_quantity += trade_quantity
    sell_order.filled_quantity += trade_quantity
    buy_wallet.balance += crypto_amount
    sell_wallet.balance += fiat_amount
    Trade.objects.create(...)
    
    # If ANY step fails, ALL are rolled back
```

**NoSQL doesn't provide this guarantee** - we can't risk partial trades.

### Why Django Over FastAPI/Flask?

**Django provides:**
- Built-in admin panel (critical for compliance/monitoring)
- ORM with excellent query optimisation
- Mature security features out of the box
- Large ecosystem of packages
- Better for large, long-term projects
- Built-in user authentication and permissions

**FastAPI is faster**, but Django's reliability and features matter more for financial services.

---

## Code Style Guide

### British English Spelling

```python
# ✅ CORRECT
user_behaviour = models.CharField(max_length=100)
colour_scheme = models.CharField(max_length=50)
is_authorised = models.BooleanField(default=False)
organisation_name = models.CharField(max_length=200)

def analyse_trading_patterns():
    """Analyse user trading behaviour."""
    pass

def serialise_order_data():
    """Serialise order to JSON format."""
    pass

# ❌ INCORRECT
user_behavior = models.CharField(max_length=100)  # American spelling
color_scheme = models.CharField(max_length=50)    # American spelling
is_authorized = models.BooleanField(default=False) # American spelling
```

### Naming Conventions

```python
# Classes: PascalCase
class OrderExecutionService:
    pass

# Functions/Methods: snake_case
def calculate_trading_fee(amount: Decimal) -> Decimal:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_WITHDRAWAL_AMOUNT = Decimal('100000.00')
REQUIRED_CONFIRMATIONS = 12

# Private methods: _leading_underscore
def _internal_helper_method(self):
    pass

# Variables: snake_case
user_balance = Decimal('1000.00')
order_count = 10
```

### Type Hints (Required)

```python
# ✅ GOOD: Clear type hints
def calculate_fee(
    amount: Decimal,
    fee_rate: Decimal,
    fee_type: str
) -> Decimal:
    """
    Calculate trading fee.
    
    Args:
        amount: Transaction amount
        fee_rate: Fee rate as decimal (e.g., 0.001 for 0.1%)
        fee_type: Either 'MAKER' or 'TAKER'
    
    Returns:
        Fee amount
    """
    return amount * fee_rate

# ❌ BAD: No type hints
def calculate_fee(amount, fee_rate, fee_type):
    return amount * fee_rate
```

### Error Handling

```python
# ✅ GOOD: Specific exceptions with context
class InsufficientBalanceError(Exception):
    """Raised when user has insufficient balance for operation."""
    
    def __init__(self, required: Decimal, available: Decimal):
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient balance: required {required}, "
            f"available {available}"
        )

def place_order(user: User, amount: Decimal):
    wallet = user.get_wallet('GBP')
    
    if wallet.available_balance < amount:
        raise InsufficientBalanceError(
            required=amount,
            available=wallet.available_balance
        )
    
    # Continue with order placement

# ❌ BAD: Generic exceptions without context
def place_order(user, amount):
    wallet = user.get_wallet('GBP')
    
    if wallet.available_balance < amount:
        raise Exception("Not enough money")  # Vague!
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# ✅ GOOD: Structured logging with context
def execute_trade(trade_id: str, buy_order_id: str, sell_order_id: str):
    logger.info(
        "Executing trade",
        extra={
            'trade_id': trade_id,
            'buy_order_id': buy_order_id,
            'sell_order_id': sell_order_id,
            'action': 'trade_execution_started'
        }
    )
    
    try:
        # Execute trade logic
        logger.info(
            "Trade executed successfully",
            extra={'trade_id': trade_id, 'action': 'trade_execution_success'}
        )
    except Exception as e:
        logger.error(
            "Trade execution failed",
            extra={
                'trade_id': trade_id,
                'error': str(e),
                'action': 'trade_execution_failed'
            },
            exc_info=True
        )
        raise

# ❌ BAD: Unstructured logging
def execute_trade(trade_id, buy_order_id, sell_order_id):
    print(f"Executing trade {trade_id}")  # Don't use print!
    # Execute trade
    logger.info("Trade done")  # Too vague
```

---

## Security Best Practices

### 1. Never Store Secrets in Code

```python
# ❌ NEVER DO THIS
SECRET_KEY = 'django-insecure-hardcoded-key-12345'
DATABASE_PASSWORD = 'mypassword123'
API_KEY = 'sk_live_abc123xyz'

# ✅ ALWAYS USE ENVIRONMENT VARIABLES
import os
from decouple import config

SECRET_KEY = config('SECRET_KEY')
DATABASE_PASSWORD = config('DATABASE_PASSWORD')
API_KEY = config('API_KEY')

# .env file (NEVER commit to git)
SECRET_KEY=randomly-generated-secure-key
DATABASE_PASSWORD=complex-password-here
API_KEY=sk_live_abc123xyz
```

### 2. Input Validation

```python
# ✅ GOOD: Validate everything
from decimal import Decimal, InvalidOperation
from django.core.validators import MinValueValidator, MaxValueValidator

class OrderSerializer(serializers.ModelSerializer):
    quantity = serializers.DecimalField(
        max_digits=20,
        decimal_places=8,
        validators=[
            MinValueValidator(Decimal('0.00000001')),
            MaxValueValidator(Decimal('1000000.0'))
        ]
    )
    
    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be positive")
        return value
    
    def validate(self, data):
        # Cross-field validation
        if data['quantity'] * data['price'] < Decimal('10.00'):
            raise serializers.ValidationError(
                "Minimum order value is £10.00"
            )
        return data

# ❌ BAD: Trusting user input
def place_order(request):
    quantity = request.data['quantity']  # Could be anything!
    order = Order.objects.create(quantity=quantity)  # Dangerous
```

### 3. SQL Injection Prevention

```python
# ✅ GOOD: Use ORM or parameterised queries
orders = Order.objects.filter(
    user=user,
    status='OPEN'
)

# Or with raw SQL (parameterised)
cursor.execute(
    "SELECT * FROM orders WHERE user_id = %s AND status = %s",
    [user_id, 'OPEN']
)

# ❌ NEVER DO THIS
query = f"SELECT * FROM orders WHERE user_id = {user_id}"  # SQL injection!
cursor.execute(query)
```

### 4. Authentication & Authorisation

```python
# ✅ GOOD: Check permissions
class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Users can only see their own orders
        return Order.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # Automatically set user to current user
        serializer.save(user=self.request.user)

# ❌ BAD: No permission checks
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()  # Returns ALL orders!
```

### 5. Rate Limiting

```python
# ✅ GOOD: Protect against abuse
from rest_framework.throttling import UserRateThrottle

class OrderRateThrottle(UserRateThrottle):
    rate = '100/hour'  # 100 orders per hour per user

class OrderViewSet(viewsets.ModelViewSet):
    throttle_classes = [OrderRateThrottle]
    
    # Also implement IP-based rate limiting for public endpoints
```

### 6. Password Security

```python
# ✅ GOOD: Use Django's built-in password handling
from django.contrib.auth.hashers import make_password, check_password

# Django automatically uses bcrypt
user.password = make_password('user_input_password')
user.save()

# Checking password
is_valid = check_password('user_input_password', user.password)

# ❌ NEVER DO THIS
import hashlib
user.password = hashlib.md5(password.encode()).hexdigest()  # Broken!
user.password = hashlib.sha256(password.encode()).hexdigest()  # Still bad!
```

---

## Testing Requirements

### Code Coverage: Minimum 80%

```python
# Every service must have comprehensive tests

# tests/test_order_service.py
import pytest
from decimal import Decimal
from trading.services import OrderExecutionService
from trading.models import Order, TradingPair, User, Wallet

@pytest.fixture
def setup_trading_environment(db):
    """Create test users, wallets, and trading pairs."""
    user_a = User.objects.create_user('user_a@test.com', 'password')
    user_b = User.objects.create_user('user_b@test.com', 'password')
    
    # Create wallets with balances
    Wallet.objects.create(
        user=user_a,
        currency='GBP',
        balance=Decimal('10000.00')
    )
    Wallet.objects.create(
        user=user_b,
        currency='BTC',
        balance=Decimal('1.0')
    )
    
    pair = TradingPair.objects.create(
        symbol='BTC/GBP',
        base_currency='BTC',
        quote_currency='GBP'
    )
    
    return user_a, user_b, pair

class TestOrderExecution:
    """Test order execution service."""
    
    def test_buy_order_matches_sell_order(self, setup_trading_environment):
        """Test that buy and sell orders match correctly."""
        user_a, user_b, pair = setup_trading_environment
        
        # User B places sell order
        sell_order = Order.objects.create(
            user=user_b,
            pair=pair,
            side='SELL',
            order_type='LIMIT',
            price=Decimal('50000.00'),
            quantity=Decimal('0.1')
        )
        
        # User A places buy order
        buy_order = Order.objects.create(
            user=user_a,
            pair=pair,
            side='BUY',
            order_type='LIMIT',
            price=Decimal('50000.00'),
            quantity=Decimal('0.1')
        )
        
        # Execute
        service = OrderExecutionService()
        result = service.execute_order(buy_order)
        
        # Assertions
        assert result.trades_executed == 1
        assert buy_order.status == 'FILLED'
        assert sell_order.status == 'FILLED'
        
        # Check balances updated
        user_a_btc = Wallet.objects.get(user=user_a, currency='BTC')
        assert user_a_btc.balance == Decimal('0.1')
        
        user_a_gbp = Wallet.objects.get(user=user_a, currency='GBP')
        assert user_a_gbp.balance == Decimal('5000.00')  # 10000 - 5000
    
    def test_insufficient_balance_raises_error(self, setup_trading_environment):
        """Test that orders with insufficient balance are rejected."""
        user_a, _, pair = setup_trading_environment
        
        # Try to buy more than balance allows
        with pytest.raises(InsufficientBalanceError):
            service = OrderExecutionService()
            service.place_order(
                user=user_a,
                pair=pair,
                side='BUY',
                price=Decimal('50000.00'),
                quantity=Decimal('1.0')  # Would cost 50,000 but only has 10,000
            )
```

### Test Categories

```python
# Unit Tests: Test individual functions/methods
def test_calculate_trading_fee():
    fee = calculate_trading_fee(
        amount=Decimal('1000.00'),
        rate=Decimal('0.001')
    )
    assert fee == Decimal('1.00')

# Integration Tests: Test multiple components together
def test_order_execution_updates_balances(db):
    # Tests that order execution correctly updates wallets
    pass

# End-to-End Tests: Test complete user flows
def test_complete_trading_flow(api_client, authenticated_user):
    # User deposits -> places order -> order matches -> withdrawal
    pass

# Security Tests: Test for vulnerabilities
def test_user_cannot_access_other_users_orders(api_client):
    # Ensure proper authorisation
    pass
```

---

## Documentation Requirements

### Every Function Must Have Docstring

```python
def calculate_order_total(
    price: Decimal,
    quantity: Decimal,
    fee_rate: Decimal
) -> Decimal:
    """
    Calculate total cost of an order including fees.
    
    Formula: (price * quantity) * (1 + fee_rate)
    
    Args:
        price: Price per unit in quote currency
        quantity: Number of units to purchase
        fee_rate: Trading fee as decimal (e.g., 0.001 for 0.1%)
    
    Returns:
        Total cost including fees
    
    Raises:
        ValueError: If any input is negative
    
    Example:
        >>> calculate_order_total(
        ...     price=Decimal('50000.00'),
        ...     quantity=Decimal('0.1'),
        ...     fee_rate=Decimal('0.001')
        ... )
        Decimal('5005.00')
    """
    if price < 0 or quantity < 0 or fee_rate < 0:
        raise ValueError("All inputs must be non-negative")
    
    subtotal = price * quantity
    fee = subtotal * fee_rate
    return subtotal + fee
```

### Complex Logic Requires Comments

```python
def match_order(self, new_order: Order) -> List[Trade]:
    """
    Match a new order against the order book.
    
    Uses price-time priority algorithm:
    1. Best price gets priority
    2. At same price, oldest order gets priority
    """
    trades = []
    
    # Get opposite side of order book
    # If new order is BUY, we match against SELL orders (asks)
    # If new order is SELL, we match against BUY orders (bids)
    opposite_side = 'asks' if new_order.side == 'BUY' else 'bids'
    
    # Iterate through opposite orders (sorted by price-time priority)
    for existing_order in self.order_book[opposite_side][:]:
        # Stop if new order is completely filled
        if new_order.remaining_quantity == 0:
            break
        
        # Check if orders can match (price criteria met)
        if self._can_match(new_order, existing_order):
            # Execute trade between these two orders
            trade = self._execute_trade(new_order, existing_order)
            trades.append(trade)
            
            # Remove fully filled orders from book
            if existing_order.remaining_quantity == 0:
                self.order_book[opposite_side].remove(existing_order)
    
    return trades
```

---

## Git Workflow

### Conventional Commits

```bash
# Format: <type>(<scope>): <subject>

# Types:
feat:     New feature
fix:      Bug fix
docs:     Documentation only
style:    Formatting, no code change
refactor: Code change that neither fixes bug nor adds feature
test:     Adding tests
chore:    Maintenance

# Examples:
git commit -m "feat(trading): add stop-limit order type"
git commit -m "fix(wallet): correct balance calculation for partial fills"
git commit -m "docs(api): update order placement endpoint documentation"
git commit -m "test(matching): add tests for price-time priority"
git commit -m "refactor(services): extract order validation to separate service"
```

### Branch Naming

```bash
# Format: <type>/<ticket-id>-<description>

feature/EXCH-123-add-stop-loss-orders
bugfix/EXCH-456-fix-withdrawal-validation
hotfix/EXCH-789-security-patch
docs/EXCH-012-api-documentation
```

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] New feature
- [ ] Bug fix
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Security Considerations
- [ ] Input validation added
- [ ] Authorisation checks added
- [ ] No secrets in code
- [ ] SQL injection prevented

## Checklist
- [ ] Code follows style guide
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No console.log or print() statements
- [ ] Type hints added (Python)
- [ ] Error handling implemented
```

---

## What We're Building (Phases)

### Phase 1: Foundation (Months 1-3) ✓
- User authentication with 2FA
- Wallet system (testnet)
- Basic order placement
- Simple matching engine
- Admin dashboard

### Phase 2: Core Trading (Months 3-6)
- Advanced order types (stop-loss, etc.)
- Real-time WebSocket feeds
- Price charts
- Deposit/withdrawal automation
- KYC/AML system foundation

### Phase 3: Compliance & Security (Months 6-9)
- External security audit
- Penetration testing
- Comprehensive audit logging
- FCA application preparation
- Documentation completion

### Phase 4: Pre-Launch (Months 9-12)
- FCA application submission
- Banking relationships
- Paper trading competition (public testing)
- Load testing and optimisation
- Production infrastructure setup

### Phase 5: Controlled Launch (Months 12-18)
- FCA approval received
- Soft launch (50-100 users)
- Gradual expansion
- Continuous monitoring
- Full public launch

---

## What Success Looks Like

### Technical Excellence
- ✅ Zero-downtime deployments
- ✅ Sub-100ms order execution
- ✅ 99.99% uptime
- ✅ Handle 10,000+ concurrent users
- ✅ Process 1,000+ orders per second
- ✅ Zero security incidents

### Code Quality
- ✅ 80%+ test coverage
- ✅ Zero critical security vulnerabilities
- ✅ All code reviewed before merge
- ✅ Comprehensive documentation
- ✅ Clean, maintainable codebase

### Regulatory Compliance
- ✅ FCA registration achieved
- ✅ Full KYC/AML compliance
- ✅ Regular audits passed
- ✅ Customer funds protected
- ✅ GDPR compliant

### Business Success
- ✅ 10,000+ registered users (Year 1)
- ✅ £1M+ daily trading volume
- ✅ Profitable operations
- ✅ Positive customer reviews
- ✅ Zero regulatory issues

---

## Anti-Patterns to Avoid

### ❌ Don't Do These

```python
# 1. God Objects (classes that do everything)
class Exchange:
    def __init__(self):
        self.users = []
        self.orders = []
        self.trades = []
        self.wallets = {}
    
    def register_user(self): pass
    def place_order(self): pass
    def match_orders(self): pass
    def execute_trade(self): pass
    def deposit(self): pass
    def withdraw(self): pass
    # 50 more methods...

# 2. Magic Numbers
if user.balance > 10000:  # What is 10000?
    apply_vip_status()

# 3. Nested Conditionals
if user:
    if user.is_verified:
        if user.balance > 0:
            if order.price > 0:
                # Deep nesting is hard to read
                pass

# 4. Mutable Default Arguments
def create_order(tags=[]):  # ❌ Dangerous!
    tags.append('new')
    return tags

# 5. Ignoring Errors
try:
    execute_trade()
except Exception:
    pass  # ❌ Silent failure!

# 6. String Concatenation for SQL
query = "SELECT * FROM users WHERE id=" + user_id  # ❌ SQL injection!

# 7. Storing Passwords Incorrectly
user.password = hashlib.sha256(password).hexdigest()  # ❌ Not secure!

# 8. No Type Hints
def calculate(a, b, c):  # ❌ What are these?
    return a * b + c

# 9. Cryptic Variable Names
def calc(x, y, z):  # ❌ Unclear
    return (x * y) - z

# 10. Comments That Lie
# Add 1 to counter
counter -= 1  # ❌ Comment doesn't match code!
```

---

## Key Mantras

### 1. "Security is not optional"
Every line of code must consider security implications.

### 2. "Simplicity is sophistication"
The simplest solution is usually the best solution.

### 3. "Test everything"
If it's not tested, it's broken.

### 4. "Document for your future self"
You'll read this code in 6 months and need to understand it.

### 5. "Fail fast, fail loud"
Don't hide errors - expose them immediately.

### 6. "Compliance is a feature, not a burden"
Regulatory compliance protects our users and our business.

### 7. "Users' money is sacred"
We handle real money - one mistake can ruin lives.

### 8. "When in doubt, ask"
No question is stupid when it comes to security or compliance.

---

## Resources & References

### Official Documentation
- Django: https://docs.djangoproject.com/
- Django REST Framework: https://www.django-rest-framework.org/
- Web3.py: https://web3py.readthedocs.io/
- PostgreSQL: https://www.postgresql.org/docs/

### Regulatory Resources
- FCA Cryptoasset Registration: https://www.fca.org.uk/firms/cryptoasset-registration
- FCA Guidance: https://www.fca.org.uk/firms/financial-crime/cryptoassets
- UK MLR 2017: Money Laundering Regulations

### Security Resources
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Django Security: https://docs.djangoproject.com/en/5.0/topics/security/
- Web3 Security: https://consensys.github.io/smart-contract-best-practices/

### Learning Resources
- Clean Code by Robert C. Martin
- The Pragmatic Programmer by Hunt & Thomas
- Python Testing with pytest by Brian Okken

---

## Contact & Support

### For Questions About:

**Architecture & Design:**
- Review SOLID principles above
- Check existing code patterns
- Ask in team meetings

**Security Concerns:**
- Never ignore security questions
- Document all security decisions
- External audit for major changes

**Regulatory Compliance:**
- Consult with legal team
- Document all compliance decisions
- When in doubt, be conservative

**Code Review:**
- All code must be reviewed
- Security-critical code needs 2+ reviewers
- Financial logic needs extra scrutiny

---

## Code Style: Write Like a Human

**Write code like a mid-senior developer, not a textbook or AI.**

### Do This
- **Minimal docs**: Only document non-obvious logic. Skip docstrings on simple getters/setters
- **Terse names in tight scope**: `amt` not `transaction_amount` in a 5-line function
- **Imperfect consistency**: Don't obsess over identical patterns everywhere
- **Sparse logging**: Log errors and key business events only, not every operation
- **Skip obvious type hints**: Don't annotate `return True` or simple one-liners
- **No section dividers**: No `# ========` banners between code sections
- **Real comments**: `# hack for legacy API` not `# This elegantly transforms...`
- **Leave TODOs**: `# TODO: handle edge case` is realistic
- **Be pragmatic**: If it's obvious, don't explain it

### Don't Do This
- Docstring on every single method
- Logging every operation (deposit started, deposit completed, etc.)
- Perfectly identical patterns everywhere
- Over-defensive code checking impossible states
- Verbose names like `user_authentication_validation_result`
- Example usage in every docstring
- Type hints on trivial returns

### The Goal
Code should look like it was written by a competent developer who:
- Has deadlines
- Knows some things are obvious
- Has personal style preferences
- Sometimes takes shortcuts (within reason)
- Adds docs when they'll actually help future readers

**Security and correctness are still non-negotiable** - but we don't need to document that `get_wallet()` gets a wallet.

---

## Conclusion

We're building something important. This platform will handle real money for real people. Every line of code we write could affect someone's financial security.

**We don't take shortcuts.**
**We don't compromise on security.**
**We don't skip tests.**
**We don't ignore regulations.**

We write **professional, secure, maintainable code** that we can be proud of.

---

*Last Updated: November 2024*
*Next Review: January 2025*
