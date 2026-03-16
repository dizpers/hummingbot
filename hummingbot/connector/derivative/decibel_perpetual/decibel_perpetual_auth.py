from typing import Optional

from aptos_sdk.account import Account
from aptos_sdk.account_address import AccountAddress
from aptos_sdk.ed25519 import PrivateKey


class DecibelPerpetualAuth:
    """
    Authentication class for Decibel Perpetual connector.

    Decibel uses delegation pattern (like Pacifica):
    - API wallet signs all transactions
    - Main wallet delegates trading permissions to API wallet
    - Main wallet private key is NEVER exposed to the bot

    This class manages the API wallet account for signing and derives
    the subaccount address from the main wallet public key.
    """

    def __init__(self, api_wallet_private_key: str, main_wallet_public_key: str):
        """
        Initialize authentication with API wallet keypair and main wallet public key.

        :param api_wallet_private_key: API wallet private key (hex format, with or without 0x prefix)
        :param main_wallet_public_key: Main wallet public key (for subaccount derivation)
        """
        self._api_wallet_private_key_hex = api_wallet_private_key.replace("0x", "").replace("0X", "")
        self._main_wallet_public_key = main_wallet_public_key.replace("0x", "").replace("0X", "")
        self._api_wallet_account: Optional[Account] = None
        self._subaccount_addr: Optional[str] = None

    @property
    def account(self) -> Account:
        """
        Get the API wallet account instance (used for signing transactions).
        Lazy initialization to avoid creating account on import.
        """
        if self._api_wallet_account is None:
            private_key = PrivateKey.from_hex(self._api_wallet_private_key_hex)
            self._api_wallet_account = Account.load_key(private_key.hex())
        return self._api_wallet_account

    @property
    def address(self) -> str:
        """
        Get the API wallet address (0x... format).
        This is the wallet that signs transactions.
        """
        return str(self.account.address())

    @property
    def main_wallet_address(self) -> str:
        """
        Get the main wallet address from public key.
        This is used for subaccount derivation.
        """
        # Main wallet address is the public key with 0x prefix
        return f"0x{self._main_wallet_public_key}"

    def get_subaccount_address(self, package_address: str) -> str:
        """
        Get the primary subaccount address derived from MAIN wallet.

        In Decibel, all trading operations are done through subaccounts.
        The primary subaccount is derived from the MAIN wallet address,
        not the API wallet address.

        :param package_address: The Decibel package address on Aptos
        :return: The subaccount address
        """
        if self._subaccount_addr is None:
            # Derive primary subaccount address from MAIN wallet
            creator = AccountAddress.from_str(self.main_wallet_address)
            # Primary subaccount uses empty seed (b"")
            seed = b""
            subaccount = AccountAddress.for_named_object(creator, seed)
            self._subaccount_addr = str(subaccount)

        return self._subaccount_addr

    def sign_transaction(self, transaction) -> any:
        """
        Sign a transaction with the API wallet's private key.

        The API wallet has been delegated permission to trade on behalf
        of the main wallet's subaccount.

        :param transaction: The transaction to sign
        :return: The signed transaction authenticator
        """
        return transaction.sign(self.account.private_key)

    async def rest_authenticate(self, request):
        """
        REST API authentication is handled via API key (Bearer token) in headers.
        This method is required by the framework but does nothing since
        authentication is handled in the connector's _api_request method.

        :param request: The request to authenticate
        :return: The request unchanged
        """
        return request
