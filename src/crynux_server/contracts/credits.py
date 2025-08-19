from typing import TYPE_CHECKING, List, Optional, Tuple

from eth_typing import ChecksumAddress
from web3 import AsyncWeb3, Web3

from crynux_server.models import ChainNodeInfo, ChainNodeStatus, GpuInfo

from .utils import ContractWrapper, TxWaiter
from .w3_pool import W3Pool

if TYPE_CHECKING:
    from crynux_server.config import TxOption


__all__ = ["CreditsContract"]


class CreditsContract(ContractWrapper):
    def __init__(
        self, w3_pool: W3Pool, contract_address: Optional[ChecksumAddress] = None
    ):
        super().__init__(w3_pool, "Credits", contract_address)

    async def set_admin_address(
        self,
        admin_address: ChecksumAddress,
        *,
        option: "Optional[TxOption]" = None,
        w3: Optional[AsyncWeb3] = None,
    ):
        return await self._transaction_call(
            "setAdminAddress",
            adminAddress=admin_address,
            option=option,
            w3=w3,
        )

    async def set_staking_address(
        self,
        staking_address: ChecksumAddress,
        *,
        option: "Optional[TxOption]" = None,
        w3: Optional[AsyncWeb3] = None,
    ):
        return await self._transaction_call(
            "setStakingAddress",
            stakingAddress=staking_address,
            option=option,
            w3=w3,
        )

    async def get_credits(
        self, addr: ChecksumAddress, *, w3: Optional[AsyncWeb3] = None
    ) -> int:
        return await self._function_call(
            "getCredits",
            addr=addr,
            w3=w3,
        )

    async def get_all_credit_addresses(
        self, *, w3: Optional[AsyncWeb3] = None
    ) -> List[ChecksumAddress]:
        return await self._function_call(
            "getAllCreditAddresses",
            w3=w3,
        )

    async def get_all_credits(
        self, *, w3: Optional[AsyncWeb3] = None
    ) -> Tuple[List[ChecksumAddress], List[int]]:
        return await self._function_call(
            "getAllCredits",
            w3=w3,
        )

    async def create_credits(
        self,
        addr: ChecksumAddress,
        amount: int,
        *,
        option: "Optional[TxOption]" = None,
        w3: Optional[AsyncWeb3] = None,
    ):
        return await self._transaction_call(
            "createCredits",
            addr=addr,
            amount=amount,
            option=option,
            w3=w3,
        )
