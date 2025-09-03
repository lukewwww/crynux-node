from typing import TYPE_CHECKING, Optional

from eth_typing import ChecksumAddress
from web3 import AsyncWeb3, Web3

from .utils import ContractWrapper, TxWaiter
from .w3_pool import W3Pool

if TYPE_CHECKING:
    from crynux_server.config import TxOption


__all__ = ["BenefitAddressContract"]


class BenefitAddressContract(ContractWrapper):
    def __init__(
        self, w3_pool: W3Pool, contract_address: Optional[ChecksumAddress] = None
    ):
        super().__init__(w3_pool, "BenefitAddress", contract_address)

    async def set_benefit_address(
        self,
        benefit_address: ChecksumAddress,
        *,
        option: "Optional[TxOption]" = None,
        w3: Optional[AsyncWeb3] = None,
    ):
        return await self._transaction_call(
            "setBenefitAddress",
            benefitAddress=benefit_address,
            option=option,
            w3=w3,
        )

    async def get_benefit_address(
        self, node_address: ChecksumAddress, *, w3: Optional[AsyncWeb3] = None
    ) -> ChecksumAddress:
        return await self._function_call(
            "getBenefitAddress",
            nodeAddress=node_address,
            w3=w3,
        )
