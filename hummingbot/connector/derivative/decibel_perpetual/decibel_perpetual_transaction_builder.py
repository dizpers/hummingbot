"""
Transaction builder for Decibel Perpetual on-chain operations.

Uses Decibel Python SDK for order placement and cancellation.
"""

import time
from typing import Optional, Tuple

from decibel import MAINNET_CONFIG, TESTNET_CONFIG, BaseSDKOptions, DecibelWriteDex, TimeInForce

from hummingbot.connector.derivative.decibel_perpetual.decibel_perpetual_auth import DecibelPerpetualAuth
from hummingbot.logger import HummingbotLogger


class DecibelPerpetualTransactionBuilder:
    """
    Builds and submits Aptos transactions for Decibel Perpetual operations using Decibel SDK.
    """

    _logger: Optional[HummingbotLogger] = None

    def __init__(
        self,
        auth: DecibelPerpetualAuth,
        package_address: str,
        fullnode_url: str,
        domain: str = "decibel_perpetual",
    ):
        """
        Initialize transaction builder.

        :param auth: Authentication instance
        :param package_address: Decibel package address on Aptos
        :param fullnode_url: Aptos fullnode URL for transaction submission
        :param domain: Domain (mainnet or testnet)
        """
        self._auth = auth
        self._package_address = package_address
        self._fullnode_url = fullnode_url
        self._domain = domain
        self._write_dex: Optional[DecibelWriteDex] = None

    @classmethod
    def logger(cls) -> HummingbotLogger:
        if cls._logger is None:
            from hummingbot.logger import HummingbotLogger
            cls._logger = HummingbotLogger(__name__)
        return cls._logger

    async def _get_write_dex(self) -> DecibelWriteDex:
        """Get or create Decibel write SDK instance."""
        if self._write_dex is None:
            from decibel import GasPriceManager

            config = TESTNET_CONFIG if "testnet" in self._domain else MAINNET_CONFIG
            account = self._auth.account

            # Initialize GasPriceManager for gas price estimation
            # Note: Gas station sponsorship requires a separate API key with service type "Gs" or "All"
            # The trading API key (service type "Api") cannot be used for gas station
            gas = GasPriceManager(config)
            await gas.initialize()

            self._write_dex = DecibelWriteDex(
                config,
                account,
                opts=BaseSDKOptions(gas_price_manager=gas)
            )
        return self._write_dex

    async def place_order(
        self,
        market_id: str,
        price: float,
        size: float,
        is_buy: bool,
        is_ioc: bool = False,
        is_post_only: bool = False,
        client_order_id: Optional[str] = None,
    ) -> Tuple[str, str, float]:
        """
        Place order on Decibel via Decibel SDK.

        :param market_id: Market identifier (e.g., "BTC-USD")
        :param price: Price in human-readable format (e.g., 95000.0)
        :param size: Size in human-readable format (e.g., 0.001)
        :param is_buy: True for buy, False for sell
        :param is_ioc: Immediate or Cancel flag
        :param is_post_only: Post-only (maker-only) flag
        :param client_order_id: Optional client order ID
        :return: (transaction_hash, exchange_order_id, timestamp)
        """
        try:
            write_dex = await self._get_write_dex()

            # Convert market_id from BTC-USD to BTC/USD format
            market_name = market_id.replace("-", "/")

            # Determine time in force
            if is_ioc:
                time_in_force = TimeInForce.ImmediateOrCancel
            elif is_post_only:
                time_in_force = TimeInForce.PostOnly
            else:
                time_in_force = TimeInForce.GoodTillCanceled

            # Get subaccount address
            subaccount_addr = self._auth.get_subaccount_address(self._package_address)

            # Place order using Decibel SDK
            result = await write_dex.place_order(
                market_name=market_name,
                price=price,
                size=size,
                is_buy=is_buy,
                time_in_force=time_in_force,
                is_reduce_only=False,
                client_order_id=client_order_id,
                subaccount_addr=subaccount_addr,
            )

            timestamp = time.time()
            tx_hash = result.tx_hash
            order_id = result.order_id if hasattr(result, 'order_id') else tx_hash

            self.logger().info(f"Submitted order transaction: {tx_hash}, order_id: {order_id}")

            return tx_hash, order_id, timestamp

        except Exception as e:
            self.logger().error(f"Error placing order: {e}", exc_info=True)
            raise

    async def cancel_order(
        self,
        market_id: str,
        order_id: str,
    ) -> Tuple[str, float]:
        """
        Cancel order on Decibel via Decibel SDK.

        :param market_id: Market identifier
        :param order_id: Order ID to cancel
        :return: (transaction_hash, timestamp)
        """
        try:
            write_dex = await self._get_write_dex()

            # Convert market_id from BTC-USD to BTC/USD format
            market_name = market_id.replace("-", "/")

            # Get subaccount address
            subaccount_addr = self._auth.get_subaccount_address(self._package_address)

            # Cancel order using Decibel SDK
            result = await write_dex.cancel_order(
                market_name=market_name,
                order_id=order_id,
                subaccount_addr=subaccount_addr,
            )

            timestamp = time.time()
            tx_hash = result.tx_hash

            self.logger().info(f"Submitted cancel transaction: {tx_hash}")

            return tx_hash, timestamp

        except Exception as e:
            self.logger().error(f"Error cancelling order: {e}", exc_info=True)
            raise

    async def close(self):
        """Close the SDK client."""
        if self._write_dex:
            # Decibel SDK doesn't require explicit cleanup
            self._write_dex = None
