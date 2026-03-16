import asyncio
import time
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from hummingbot.connector.derivative.decibel_perpetual import (
    decibel_perpetual_constants as CONSTANTS,
    decibel_perpetual_web_utils as web_utils,
)
from hummingbot.core.data_type.common import TradeType
from hummingbot.core.data_type.funding_info import FundingInfo, FundingInfoUpdate
from hummingbot.core.data_type.order_book_message import OrderBookMessage, OrderBookMessageType
from hummingbot.core.data_type.perpetual_api_order_book_data_source import PerpetualAPIOrderBookDataSource
from hummingbot.core.web_assistant.connections.data_types import RESTMethod, WSJSONRequest
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory
from hummingbot.core.web_assistant.ws_assistant import WSAssistant
from hummingbot.logger import HummingbotLogger

if TYPE_CHECKING:
    from hummingbot.connector.derivative.decibel_perpetual.decibel_perpetual_derivative import (
        DecibelPerpetualDerivative,
    )


class DecibelPerpetualAPIOrderBookDataSource(PerpetualAPIOrderBookDataSource):
    _logger: Optional[HummingbotLogger] = None

    def __init__(
        self,
        trading_pairs: List[str],
        connector: "DecibelPerpetualDerivative",
        api_factory: WebAssistantsFactory,
        domain: str = CONSTANTS.DEFAULT_DOMAIN,
    ):
        super().__init__(trading_pairs)
        self._connector = connector
        self._api_factory = api_factory
        self._domain = domain
        self._ping_task: Optional[asyncio.Task] = None

    async def get_last_traded_prices(self, trading_pairs: List[str], domain: Optional[str] = None) -> Dict[str, float]:
        """
        Get last traded prices for given trading pairs.
        """
        return await self._connector.get_last_traded_prices(trading_pairs=trading_pairs)

    def _get_headers(self) -> Dict[str, str]:
        """
        Build headers for REST requests.
        Includes API key if available for better rate limits.
        """
        headers = {}
        if hasattr(self._connector, 'api_key') and self._connector.api_key:
            headers["Authorization"] = f"Bearer {self._connector.api_key}"
        return headers

    async def _request_order_book_snapshot(self, trading_pair: str) -> Dict[str, Any]:
        """
        Request order book snapshot from Decibel REST API.

        Decibel API format:
        GET /api/v1/market_depth?market=BTC/USD&limit=100

        Response format (expected):
        {
            "bids": [[price, size], ...],
            "asks": [[price, size], ...],
            "timestamp": 1234567890000
        }
        """
        rest_assistant = await self._api_factory.get_rest_assistant()
        exchange_symbol = await self._connector.exchange_symbol_associated_to_pair(trading_pair=trading_pair)

        params = {
            "market": exchange_symbol,
            "limit": 100
        }

        response = await rest_assistant.execute_request(
            url=web_utils.public_rest_url(path_url=CONSTANTS.GET_ORDERBOOK_PATH_URL, domain=self._domain),
            params=params,
            method=RESTMethod.GET,
            throttler_limit_id=CONSTANTS.GET_ORDERBOOK_PATH_URL,
            headers=self._get_headers()
        )

        return response

    async def _order_book_snapshot(self, trading_pair: str) -> OrderBookMessage:
        """
        Create OrderBookMessage from snapshot data.
        """
        snapshot_data = await self._request_order_book_snapshot(trading_pair)

        # Extract timestamp (convert from ms to seconds if needed)
        timestamp = snapshot_data.get("timestamp", time.time() * 1000) / 1000

        return OrderBookMessage(
            OrderBookMessageType.SNAPSHOT,
            {
                "trading_pair": trading_pair,
                "update_id": timestamp,
                "bids": [(str(bid[0]), str(bid[1])) for bid in snapshot_data.get("bids", [])],
                "asks": [(str(ask[0]), str(ask[1])) for ask in snapshot_data.get("asks", [])]
            },
            timestamp=timestamp
        )

    async def get_funding_info(self, trading_pair: str) -> FundingInfo:
        """
        Get funding rate information for a trading pair.

        Decibel API format:
        GET /api/v1/market_prices?market=BTC/USD

        Response format (expected):
        {
            "market": "BTC/USD",
            "mark_px": 50000.0,
            "oracle_px": 50001.0,
            "funding_rate_bps": 5,  # basis points (EMA-smoothed)
            "open_interest": 1000000.0
        }
        """
        rest_assistant = await self._api_factory.get_rest_assistant()
        exchange_symbol = await self._connector.exchange_symbol_associated_to_pair(trading_pair=trading_pair)

        params = {"market": exchange_symbol}

        response = await rest_assistant.execute_request(
            url=web_utils.public_rest_url(path_url=CONSTANTS.GET_MARKET_PRICES_PATH_URL, domain=self._domain),
            params=params,
            method=RESTMethod.GET,
            throttler_limit_id=CONSTANTS.GET_MARKET_PRICES_PATH_URL,
            headers=self._get_headers()
        )

        # Convert funding rate from basis points to decimal
        # 5 bps = 0.05% = 0.0005
        funding_rate_bps = response.get("funding_rate_bps", 0)
        funding_rate = Decimal(str(funding_rate_bps)) / Decimal("10000")

        # Mark price
        mark_price = Decimal(str(response.get("mark_px", 0)))

        # Index price (oracle price in Decibel)
        index_price = Decimal(str(response.get("oracle_px", 0)))

        # Next funding time (typically every hour, at :00)
        current_time = int(time.time())
        next_funding_time = ((current_time // 3600) + 1) * 3600

        return FundingInfo(
            trading_pair=trading_pair,
            index_price=index_price,
            mark_price=mark_price,
            next_funding_utc_timestamp=next_funding_time,
            rate=funding_rate,
        )

    async def _connected_websocket_assistant(self) -> WSAssistant:
        """
        Create and connect WebSocket assistant.
        """
        ws_url = web_utils.wss_url(domain=self._domain)
        ws_assistant = await self._api_factory.get_ws_assistant()
        await ws_assistant.connect(ws_url=ws_url, ping_timeout=CONSTANTS.WS_PING_INTERVAL)
        return ws_assistant

    async def _subscribe_channels(self, ws_assistant: WSAssistant):
        """
        Subscribe to public WebSocket channels.

        Decibel WebSocket subscription format:
        {
            "method": "subscribe",
            "params": {
                "topic": "market_depth:BTC/USD"
            }
        }
        """
        try:
            for trading_pair in self._trading_pairs:
                exchange_symbol = await self._connector.exchange_symbol_associated_to_pair(trading_pair=trading_pair)

                # Subscribe to order book updates
                subscribe_orderbook_request = WSJSONRequest({
                    "method": "subscribe",
                    "params": {
                        "topic": f"{CONSTANTS.WS_MARKET_DEPTH_CHANNEL}:{exchange_symbol}"
                    }
                })
                await ws_assistant.send(subscribe_orderbook_request)

                # Subscribe to trades
                subscribe_trades_request = WSJSONRequest({
                    "method": "subscribe",
                    "params": {
                        "topic": f"{CONSTANTS.WS_MARKET_TRADES_CHANNEL}:{exchange_symbol}"
                    }
                })
                await ws_assistant.send(subscribe_trades_request)

                # Subscribe to prices (for funding rate updates)
                subscribe_prices_request = WSJSONRequest({
                    "method": "subscribe",
                    "params": {
                        "topic": f"{CONSTANTS.WS_MARKET_PRICE_CHANNEL}:{exchange_symbol}"
                    }
                })
                await ws_assistant.send(subscribe_prices_request)

            self.logger().info("Subscribed to all public channels")

        except asyncio.CancelledError:
            raise
        except Exception:
            self.logger().exception("Unexpected error occurred subscribing to order book data streams.")
            raise

    async def _process_websocket_messages(self, websocket_assistant: WSAssistant):
        """
        Process incoming WebSocket messages.
        """
        async for ws_response in websocket_assistant.iter_messages():
            data = ws_response.data

            # Skip subscription confirmation messages
            if isinstance(data, dict) and data.get("method") in ["subscribe", "unsubscribe"]:
                continue

            # Process order book updates
            if "topic" in data and CONSTANTS.WS_MARKET_DEPTH_CHANNEL in data["topic"]:
                await self._process_order_book_message(data)

            # Process trade messages
            elif "topic" in data and CONSTANTS.WS_MARKET_TRADES_CHANNEL in data["topic"]:
                await self._process_trade_message(data)

            # Process funding rate updates
            elif "topic" in data and CONSTANTS.WS_MARKET_PRICE_CHANNEL in data["topic"]:
                await self._process_funding_info_message(data)

    async def _process_order_book_message(self, message: Dict[str, Any]):
        """
        Process order book update message.
        """
        # Extract trading pair from topic
        topic = message.get("topic", "")
        exchange_symbol = topic.split(":")[-1] if ":" in topic else ""
        trading_pair = await self._connector.trading_pair_associated_to_exchange_symbol(exchange_symbol)

        data = message.get("data", {})
        timestamp = data.get("timestamp", time.time() * 1000) / 1000

        order_book_message = OrderBookMessage(
            OrderBookMessageType.DIFF,
            {
                "trading_pair": trading_pair,
                "update_id": timestamp,
                "bids": [(str(bid[0]), str(bid[1])) for bid in data.get("bids", [])],
                "asks": [(str(ask[0]), str(ask[1])) for ask in data.get("asks", [])]
            },
            timestamp=timestamp
        )

        self._message_queue[self._diff_messages_queue_key].put_nowait(order_book_message)

    async def _process_trade_message(self, message: Dict[str, Any]):
        """
        Process trade message.
        """
        topic = message.get("topic", "")
        exchange_symbol = topic.split(":")[-1] if ":" in topic else ""
        trading_pair = await self._connector.trading_pair_associated_to_exchange_symbol(exchange_symbol)

        data = message.get("data", {})

        for trade in data.get("trades", []):
            trade_message = OrderBookMessage(
                OrderBookMessageType.TRADE,
                {
                    "trading_pair": trading_pair,
                    "trade_type": TradeType.BUY.value if trade.get("is_buy") else TradeType.SELL.value,
                    "trade_id": trade.get("trade_id"),
                    "update_id": trade.get("timestamp", time.time() * 1000),
                    "price": str(trade.get("price")),
                    "amount": str(trade.get("size"))
                },
                timestamp=trade.get("timestamp", time.time() * 1000) / 1000
            )
            self._message_queue[self._trade_messages_queue_key].put_nowait(trade_message)

    async def _process_funding_info_message(self, message: Dict[str, Any]):
        """
        Process funding rate update message.
        """
        topic = message.get("topic", "")
        exchange_symbol = topic.split(":")[-1] if ":" in topic else ""
        trading_pair = await self._connector.trading_pair_associated_to_exchange_symbol(exchange_symbol)

        data = message.get("data", {})

        funding_rate_bps = data.get("funding_rate_bps", 0)
        funding_rate = Decimal(str(funding_rate_bps)) / Decimal("10000")

        funding_info = FundingInfoUpdate(trading_pair=trading_pair, rate=funding_rate)
        self._message_queue[self._funding_info_messages_queue_key].put_nowait(funding_info)

    async def _ping_websocket(self, ws_assistant: WSAssistant):
        """
        Send periodic ping to keep WebSocket connection alive.
        """
        while True:
            try:
                await asyncio.sleep(CONSTANTS.WS_PING_INTERVAL)
                ping_request = WSJSONRequest({"method": "ping"})
                await ws_assistant.send(ping_request)
            except asyncio.CancelledError:
                break
            except Exception:
                self.logger().exception("Unexpected error while sending ping")
                break

    def _parse_funding_info_message(self, raw_message: Dict[str, Any], message_queue: asyncio.Queue):
        """
        Parse funding info message and put into queue.
        This is called by the base class when processing funding info updates.
        """
        # The message is already processed in _process_funding_info_message
        # This method is for compatibility with base class
        pass

    async def subscribe_to_trading_pair(self, trading_pair: str):
        """
        Subscribe to a single trading pair's channels.
        Called when dynamically adding trading pairs.
        """
        if self._ws_assistant is None:
            return

        exchange_symbol = await self._connector.exchange_symbol_associated_to_pair(trading_pair=trading_pair)

        # Subscribe to order book
        subscribe_orderbook_request = WSJSONRequest({
            "method": "subscribe",
            "params": {
                "topic": f"{CONSTANTS.WS_MARKET_DEPTH_CHANNEL}:{exchange_symbol}"
            }
        })
        await self._ws_assistant.send(subscribe_orderbook_request)

        # Subscribe to trades
        subscribe_trades_request = WSJSONRequest({
            "method": "subscribe",
            "params": {
                "topic": f"{CONSTANTS.WS_MARKET_TRADES_CHANNEL}:{exchange_symbol}"
            }
        })
        await self._ws_assistant.send(subscribe_trades_request)

        # Subscribe to prices (funding)
        subscribe_prices_request = WSJSONRequest({
            "method": "subscribe",
            "params": {
                "topic": f"{CONSTANTS.WS_MARKET_PRICE_CHANNEL}:{exchange_symbol}"
            }
        })
        await self._ws_assistant.send(subscribe_prices_request)

    async def unsubscribe_from_trading_pair(self, trading_pair: str):
        """
        Unsubscribe from a single trading pair's channels.
        Called when dynamically removing trading pairs.
        """
        if self._ws_assistant is None:
            return

        exchange_symbol = await self._connector.exchange_symbol_associated_to_pair(trading_pair=trading_pair)

        # Unsubscribe from order book
        unsubscribe_orderbook_request = WSJSONRequest({
            "method": "unsubscribe",
            "params": {
                "topic": f"{CONSTANTS.WS_MARKET_DEPTH_CHANNEL}:{exchange_symbol}"
            }
        })
        await self._ws_assistant.send(unsubscribe_orderbook_request)

        # Unsubscribe from trades
        unsubscribe_trades_request = WSJSONRequest({
            "method": "unsubscribe",
            "params": {
                "topic": f"{CONSTANTS.WS_MARKET_TRADES_CHANNEL}:{exchange_symbol}"
            }
        })
        await self._ws_assistant.send(unsubscribe_trades_request)

        # Unsubscribe from prices
        unsubscribe_prices_request = WSJSONRequest({
            "method": "unsubscribe",
            "params": {
                "topic": f"{CONSTANTS.WS_MARKET_PRICE_CHANNEL}:{exchange_symbol}"
            }
        })
        await self._ws_assistant.send(unsubscribe_prices_request)
