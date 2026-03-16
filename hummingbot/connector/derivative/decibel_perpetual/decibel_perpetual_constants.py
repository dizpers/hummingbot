from decibel import MAINNET_CONFIG, TESTNET_CONFIG

from hummingbot.core.api_throttler.data_types import LinkedLimitWeightPair, RateLimit
from hummingbot.core.data_type.in_flight_order import OrderState

EXCHANGE_NAME = "decibel_perpetual"
DEFAULT_DOMAIN = "decibel_perpetual"

# Base URLs - Mainnet
REST_URL = "https://api.mainnet.aptoslabs.com/decibel"
WSS_URL = "wss://api.mainnet.aptoslabs.com/decibel/ws"
FULLNODE_URL = "https://api.mainnet.aptoslabs.com/v1"

# Testnet
TESTNET_DOMAIN = "decibel_perpetual_testnet"
TESTNET_REST_URL = "https://api.testnet.aptoslabs.com/decibel"
TESTNET_WSS_URL = "wss://api.testnet.aptoslabs.com/decibel/ws"
TESTNET_FULLNODE_URL = "https://api.testnet.aptoslabs.com/v1"

# Aptos deployment addresses - imported directly from SDK to ensure consistency
MAINNET_PACKAGE = MAINNET_CONFIG.deployment.package
TESTNET_PACKAGE = TESTNET_CONFIG.deployment.package

# Order state mapping
ORDER_STATE = {
    "Open": OrderState.OPEN,
    "Filled": OrderState.FILLED,
    "PartiallyFilled": OrderState.PARTIALLY_FILLED,
    "Cancelled": OrderState.CANCELED,
    "Rejected": OrderState.FAILED,
    "Expired": OrderState.CANCELED,
}

# REST API Endpoints
GET_MARKETS_PATH_URL = "/api/v1/markets"
GET_MARKET_PRICES_PATH_URL = "/api/v1/market_prices"
GET_ASSET_CONTEXTS_PATH_URL = "/api/v1/asset_contexts"
GET_ORDERBOOK_PATH_URL = "/api/v1/market_depth"
GET_TRADES_PATH_URL = "/api/v1/trades"
GET_CANDLESTICK_PATH_URL = "/api/v1/candlestick"

# Account endpoints
GET_ACCOUNT_OVERVIEW_PATH_URL = "/api/v1/account_overviews"
GET_ACCOUNT_POSITIONS_PATH_URL = "/api/v1/account_positions"
GET_ACCOUNT_OPEN_ORDERS_PATH_URL = "/api/v1/account_open_orders"
GET_USER_ORDER_HISTORY_PATH_URL = "/api/v1/user_order_history"
GET_USER_TRADE_HISTORY_PATH_URL = "/api/v1/user_trade_history"
GET_USER_FUNDING_HISTORY_PATH_URL = "/api/v1/user_funding_rate_history"
GET_SUBACCOUNTS_PATH_URL = "/api/v1/subaccounts"

# WebSocket Channels
# Public channels
WS_ALL_MARKET_PRICES_CHANNEL = "all_market_prices"
WS_MARKET_PRICE_CHANNEL = "market_price"
WS_MARKET_DEPTH_CHANNEL = "market_depth"
WS_MARKET_TRADES_CHANNEL = "market_trades"
WS_MARKET_CANDLESTICK_CHANNEL = "market_candlestick"

# Private channels (require subaccount address)
WS_ACCOUNT_OVERVIEW_CHANNEL = "account_overview"
WS_USER_POSITIONS_CHANNEL = "user_positions"
WS_USER_OPEN_ORDERS_CHANNEL = "account_open_orders"
WS_USER_ORDER_HISTORY_CHANNEL = "user_order_history"
WS_USER_TRADE_HISTORY_CHANNEL = "user_trade_history"
WS_USER_TRADES_CHANNEL = "user_trades"
WS_USER_FUNDING_HISTORY_CHANNEL = "user_funding_rate_history"
WS_ORDER_UPDATE_CHANNEL = "order_update"
WS_NOTIFICATIONS_CHANNEL = "notifications"

# WebSocket configuration
WS_PING_INTERVAL = 30  # seconds

# Transaction configuration
# Based on Decibel team answer: 40ms block latency, 500ms confirmation
# Using 2x confirmation time for safety margin
TX_CONFIRMATION_TIMEOUT = 1.0  # seconds (2x 500ms confirmation time)
TX_POLL_INTERVAL = 0.1  # seconds (poll every 100ms)

# Rate Limits
# Based on official Decibel documentation via Geomi
# Source: https://geomi.dev/docs/admin/billing#system-limits
# Note: All Decibel API requests require an API key (no anonymous access)
DECIBEL_LIMIT_ID = "DECIBEL_LIMIT"

# Decibel REST API rate limit (DecibelHttpApi upstream)
# 200 requests per 30 seconds = 400 requests per minute
# This applies to all market data reads (orderbook, trades, positions, etc.)
DECIBEL_API_LIMIT = 400  # requests per minute
DECIBEL_LIMIT_INTERVAL = 60  # seconds

# Note: Transaction writes go to Aptos API directly and may have separate limits
# Aptos Node API limit: 200 req/30s (handled by Aptos SDK)

# Endpoint costs (weight per request type)
STANDARD_REQUEST_COST = 1
ORDERBOOK_REQUEST_COST = 5
HEAVY_REQUEST_COST = 10

# Single rate limit tier (API key required for all requests)
RATE_LIMITS = [
    RateLimit(limit_id=DECIBEL_LIMIT_ID, limit=DECIBEL_API_LIMIT, time_interval=DECIBEL_LIMIT_INTERVAL),
    RateLimit(limit_id=GET_MARKETS_PATH_URL, limit=DECIBEL_API_LIMIT, time_interval=DECIBEL_LIMIT_INTERVAL,
              linked_limits=[LinkedLimitWeightPair(limit_id=DECIBEL_LIMIT_ID, weight=STANDARD_REQUEST_COST)]),
    RateLimit(limit_id=GET_MARKET_PRICES_PATH_URL, limit=DECIBEL_API_LIMIT, time_interval=DECIBEL_LIMIT_INTERVAL,
              linked_limits=[LinkedLimitWeightPair(limit_id=DECIBEL_LIMIT_ID, weight=STANDARD_REQUEST_COST)]),
    RateLimit(limit_id=GET_ORDERBOOK_PATH_URL, limit=DECIBEL_API_LIMIT, time_interval=DECIBEL_LIMIT_INTERVAL,
              linked_limits=[LinkedLimitWeightPair(limit_id=DECIBEL_LIMIT_ID, weight=ORDERBOOK_REQUEST_COST)]),
    RateLimit(limit_id=GET_ACCOUNT_OVERVIEW_PATH_URL, limit=DECIBEL_API_LIMIT, time_interval=DECIBEL_LIMIT_INTERVAL,
              linked_limits=[LinkedLimitWeightPair(limit_id=DECIBEL_LIMIT_ID, weight=HEAVY_REQUEST_COST)]),
    RateLimit(limit_id=GET_ACCOUNT_POSITIONS_PATH_URL, limit=DECIBEL_API_LIMIT, time_interval=DECIBEL_LIMIT_INTERVAL,
              linked_limits=[LinkedLimitWeightPair(limit_id=DECIBEL_LIMIT_ID, weight=HEAVY_REQUEST_COST)]),
    RateLimit(limit_id=GET_ACCOUNT_OPEN_ORDERS_PATH_URL, limit=DECIBEL_API_LIMIT, time_interval=DECIBEL_LIMIT_INTERVAL,
              linked_limits=[LinkedLimitWeightPair(limit_id=DECIBEL_LIMIT_ID, weight=HEAVY_REQUEST_COST)]),
    RateLimit(limit_id=GET_USER_ORDER_HISTORY_PATH_URL, limit=DECIBEL_API_LIMIT, time_interval=DECIBEL_LIMIT_INTERVAL,
              linked_limits=[LinkedLimitWeightPair(limit_id=DECIBEL_LIMIT_ID, weight=HEAVY_REQUEST_COST)]),
    RateLimit(limit_id=GET_USER_TRADE_HISTORY_PATH_URL, limit=DECIBEL_API_LIMIT, time_interval=DECIBEL_LIMIT_INTERVAL,
              linked_limits=[LinkedLimitWeightPair(limit_id=DECIBEL_LIMIT_ID, weight=HEAVY_REQUEST_COST)]),
]
