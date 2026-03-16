from decimal import Decimal

from pydantic import ConfigDict, Field, SecretStr

from hummingbot.client.config.config_data_types import BaseConnectorConfigMap
from hummingbot.core.data_type.trade_fee import TradeFeeSchema

CENTRALIZED = True
EXAMPLE_PAIR = "BTC-USD"

# Default fees based on Decibel documentation
# Maker: ~0.015%, Taker: ~0.04%
DEFAULT_FEES = TradeFeeSchema(
    maker_percent_fee_decimal=Decimal("0.00015"),
    taker_percent_fee_decimal=Decimal("0.0004"),
)


class DecibelPerpetualConfigMap(BaseConnectorConfigMap):
    connector: str = "decibel_perpetual"

    decibel_perpetual_api_wallet_public_key: SecretStr = Field(
        default=...,
        json_schema_extra={
            "prompt": "Enter your Decibel Perpetual API Wallet Public Key",
            "is_secure": True,
            "is_connect_key": True,
            "prompt_on_new": True
        }
    )

    decibel_perpetual_api_wallet_private_key: SecretStr = Field(
        default=...,
        json_schema_extra={
            "prompt": "Enter your Decibel Perpetual API Wallet Private Key (hex format, with or without 0x prefix)",
            "is_secure": True,
            "is_connect_key": True,
            "prompt_on_new": True
        }
    )

    decibel_perpetual_main_wallet_public_key: SecretStr = Field(
        default=...,
        json_schema_extra={
            "prompt": "Enter your Decibel Perpetual Main Wallet Public Key",
            "is_secure": True,
            "is_connect_key": True,
            "prompt_on_new": True
        }
    )

    decibel_perpetual_api_key: SecretStr = Field(
        default=...,
        json_schema_extra={
            "prompt": "Enter your Decibel Perpetual API Key from geomi.dev (required for all API access)",
            "is_secure": True,
            "is_connect_key": True,
            "prompt_on_new": True
        }
    )

    decibel_perpetual_market_order_slippage: Decimal = Field(
        default=Decimal("0.08"),
        json_schema_extra={
            "prompt": "Enter market order slippage percentage (default 0.08 = 8%)",
            "prompt_on_new": False
        }
    )

    model_config = ConfigDict(title="decibel_perpetual")


KEYS = DecibelPerpetualConfigMap.model_construct()

OTHER_DOMAINS = ["decibel_perpetual_testnet"]
OTHER_DOMAINS_PARAMETER = {"decibel_perpetual_testnet": "decibel_perpetual_testnet"}
OTHER_DOMAINS_EXAMPLE_PAIR = {"decibel_perpetual_testnet": "BTC-USD"}
OTHER_DOMAINS_DEFAULT_FEES = {"decibel_perpetual_testnet": [0.00015, 0.0004]}


class DecibelPerpetualTestnetConfigMap(BaseConnectorConfigMap):
    connector: str = "decibel_perpetual_testnet"

    decibel_perpetual_testnet_api_wallet_public_key: SecretStr = Field(
        default=...,
        json_schema_extra={
            "prompt": "Enter your Decibel Perpetual Testnet API Wallet Public Key",
            "is_secure": True,
            "is_connect_key": True,
            "prompt_on_new": True
        }
    )

    decibel_perpetual_testnet_api_wallet_private_key: SecretStr = Field(
        default=...,
        json_schema_extra={
            "prompt": "Enter your Decibel Perpetual Testnet API Wallet Private Key (hex format, with or without 0x prefix)",
            "is_secure": True,
            "is_connect_key": True,
            "prompt_on_new": True
        }
    )

    decibel_perpetual_testnet_main_wallet_public_key: SecretStr = Field(
        default=...,
        json_schema_extra={
            "prompt": "Enter your Decibel Perpetual Testnet Main Wallet Public Key",
            "is_secure": True,
            "is_connect_key": True,
            "prompt_on_new": True
        }
    )

    decibel_perpetual_testnet_api_key: SecretStr = Field(
        default=...,
        json_schema_extra={
            "prompt": "Enter your Decibel Perpetual Testnet API Key from geomi.dev (required)",
            "is_secure": True,
            "is_connect_key": True,
            "prompt_on_new": True
        }
    )

    decibel_perpetual_testnet_market_order_slippage: Decimal = Field(
        default=Decimal("0.08"),
        json_schema_extra={
            "prompt": "Enter market order slippage percentage (default 0.08 = 8%)",
            "prompt_on_new": False
        }
    )

    model_config = ConfigDict(title="decibel_perpetual_testnet")


OTHER_DOMAINS_KEYS = {
    "decibel_perpetual_testnet": DecibelPerpetualTestnetConfigMap.model_construct()
}
