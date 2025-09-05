from typing import TYPE_CHECKING, Optional

from eth_typing import ChecksumAddress
from web3 import AsyncWeb3, Web3

from .utils import ContractWrapper, TxWaiter
from .w3_pool import W3Pool

if TYPE_CHECKING:
    from crynux_server.config import TxOption

__all__ = ["WithdrawContract"]


class WithdrawContract(ContractWrapper):
    def __init__(
        self, w3_pool: W3Pool, contract_address: Optional[ChecksumAddress] = None
    ):
        super().__init__(w3_pool, "Withdraw", contract_address)

    async def set_withdrawal_fee_address(
        self,
        addr: ChecksumAddress,
        *,
        option: "Optional[TxOption]" = None,
        w3: Optional[AsyncWeb3] = None,
    ):
        return await self._transaction_call(
            "setWithdrawalFeeAddress",
            addr=addr,
            option=option,
            w3=w3,
        )

    async def get_withdrawal_fee_address(
        self,
        *,
        w3: Optional[AsyncWeb3] = None,
    ) -> ChecksumAddress:
        return await self._function_call(
            "getWithdrawalFeeAddress",
            w3=w3,
        )

    async def withdraw(
        self,
        to: ChecksumAddress,
        amount: int,
        withdrawal_fee_amount: int,
        *,
        option: "Optional[TxOption]" = None,
        w3: Optional[AsyncWeb3] = None,
    ):
        return await self._transaction_call(
            "withdraw",
            to=to,
            amount=amount,
            withdrawalFeeAmount=withdrawal_fee_amount,
            value=amount + withdrawal_fee_amount,
            option=option,
            w3=w3,
        )
