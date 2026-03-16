from typing import Any, Optional

from hummingbot.connector.derivative.decibel_perpetual import decibel_perpetual_constants as CONSTANTS
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory


def public_rest_url(path_url: str, domain: str = CONSTANTS.DEFAULT_DOMAIN) -> str:
    """
    Creates a full REST URL for public endpoints.

    :param path_url: The API endpoint path
    :param domain: The domain (mainnet or testnet)
    :return: The full URL
    """
    base_url = CONSTANTS.REST_URL if domain == CONSTANTS.DEFAULT_DOMAIN else CONSTANTS.TESTNET_REST_URL
    return base_url + path_url


def private_rest_url(path_url: str, domain: str = CONSTANTS.DEFAULT_DOMAIN) -> str:
    """
    Creates a full REST URL for private endpoints.

    :param path_url: The API endpoint path
    :param domain: The domain (mainnet or testnet)
    :return: The full URL
    """
    # For Decibel, private and public endpoints use the same base URL
    return public_rest_url(path_url, domain)


def wss_url(domain: str = CONSTANTS.DEFAULT_DOMAIN) -> str:
    """
    Creates the WebSocket URL.

    :param domain: The domain (mainnet or testnet)
    :return: The WebSocket URL
    """
    return CONSTANTS.WSS_URL if domain == CONSTANTS.DEFAULT_DOMAIN else CONSTANTS.TESTNET_WSS_URL


def fullnode_url(domain: str = CONSTANTS.DEFAULT_DOMAIN) -> str:
    """
    Creates the Aptos fullnode URL for transaction submission.

    :param domain: The domain (mainnet or testnet)
    :return: The fullnode URL
    """
    return CONSTANTS.FULLNODE_URL if domain == CONSTANTS.DEFAULT_DOMAIN else CONSTANTS.TESTNET_FULLNODE_URL


def build_api_factory(
    throttler: Optional[Any] = None,
    auth: Optional[Any] = None,
) -> WebAssistantsFactory:
    """
    Builds a WebAssistantsFactory for Decibel API requests.

    :param throttler: The rate limiter
    :param auth: The authenticator (not used for REST API, only for transactions)
    :return: The WebAssistantsFactory instance
    """
    return WebAssistantsFactory(
        throttler=throttler,
        auth=auth,
    )


def get_package_address(domain: str = CONSTANTS.DEFAULT_DOMAIN) -> str:
    """
    Gets the Aptos package address for the given domain.

    :param domain: The domain (mainnet or testnet)
    :return: The package address
    """
    return CONSTANTS.MAINNET_PACKAGE if domain == CONSTANTS.DEFAULT_DOMAIN else CONSTANTS.TESTNET_PACKAGE
