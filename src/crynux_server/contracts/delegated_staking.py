from typing import TYPE_CHECKING, List, Optional, Tuple

from eth_typing import ChecksumAddress
from web3 import AsyncWeb3, Web3

from crynux_server.models import ChainNodeStakingInfo

from .utils import ContractWrapper, TxWaiter
from .w3_pool import W3Pool

if TYPE_CHECKING:
    from crynux_server.config import TxOption


__all__ = ["DelegatedStakingContract"]


class DelegatedStakingContract(ContractWrapper):
    def __init__(
        self, w3_pool: W3Pool, contract_address: Optional[ChecksumAddress] = None
    ):
        super().__init__(w3_pool, "UserStaking", contract_address)

    async def set_min_stake_amount(
        self,
        stake_amount: int,
        *,
        option: "Optional[TxOption]" = None,
        w3: Optional[AsyncWeb3] = None,
    ):
        return await self._transaction_call(
            "setMinStakeAmount",
            stakeAmount=stake_amount,
            option=option,
            w3=w3,
        )

    async def get_min_stake_amount(self, *, w3: Optional[AsyncWeb3] = None) -> int:
        return await self._function_call(
            "getMinStakeAmount",
            w3=w3,
        )

    async def set_node_staking_address(
        self,
        addr: ChecksumAddress,
        *,
        option: "Optional[TxOption]" = None,
        w3: Optional[AsyncWeb3] = None,
    ):
        return await self._transaction_call(
            "setNodeStakingAddress",
            addr=addr,
            option=option,
            w3=w3,
        )

    async def set_delegator_share(
        self,
        share: int,
        *,
        option: "Optional[TxOption]" = None,
        w3: Optional[AsyncWeb3] = None,
    ):
        return await self._transaction_call(
            "setDelegatorShare",
            share=share,
            option=option,
            w3=w3,
        )

    async def stake(
        self,
        node_address: ChecksumAddress,
        amount: int,
        *,
        value: Optional[int] = None,
        option: "Optional[TxOption]" = None,
        w3: Optional[AsyncWeb3] = None,
    ):
        return await self._transaction_call(
            "stake",
            nodeAddress=node_address,
            amount=amount,
            value=value,
            option=option,
            w3=w3,
        )

    async def unstake(
        self,
        node_address: ChecksumAddress,
        *,
        option: "Optional[TxOption]" = None,
        w3: Optional[AsyncWeb3] = None,
    ):
        return await self._transaction_call(
            "unstake",
            nodeAddress=node_address,
            option=option,
            w3=w3,
        )

    async def get_node_delegator_share(
        self,
        node_address: ChecksumAddress,
        *,
        w3: Optional[AsyncWeb3] = None,
    ) -> int:
        return await self._function_call(
            "getNodeDelegatorShare",
            nodeAddress=node_address,
            w3=w3,
        )

    async def get_all_node_delegator_shares(
        self, *, w3: Optional[AsyncWeb3] = None
    ) -> Tuple[List[ChecksumAddress], List[int]]:
        return await self._function_call("getAllNodeDelegatorShares", w3=w3)

    async def get_delegation_staking_amount(
        self,
        delegator_address: ChecksumAddress,
        node_address: ChecksumAddress,
        *,
        w3: Optional[AsyncWeb3] = None,
    ) -> int:
        return await self._function_call(
            "getDelegationStakingAmount",
            delegatorAddress=delegator_address,
            nodeAddress=node_address,
            w3=w3,
        )

    async def get_delegator_staking_infos(
        self,
        delegator_address: ChecksumAddress,
        *,
        w3: Optional[AsyncWeb3] = None,
    ) -> Tuple[List[ChecksumAddress], List[int]]:
        return await self._function_call(
            "getDelegatorStakingInfos",
            delegatorAddress=delegator_address,
            w3=w3,
        )

    async def get_node_staking_infos(
        self,
        node_address: ChecksumAddress,
        *,
        w3: Optional[AsyncWeb3] = None,
    ) -> Tuple[List[ChecksumAddress], List[int]]:
        return await self._function_call(
            "getNodeStakingInfos",
            nodeAddress=node_address,
            w3=w3,
        )

    async def get_node_total_stake_amount(
        self,
        node_address: ChecksumAddress,
        *,
        w3: Optional[AsyncWeb3] = None,
    ) -> int:
        return await self._function_call(
            "getNodeTotalStakeAmount",
            nodeAddress=node_address,
            w3=w3,
        )

    async def get_delegator_total_stake_amount(
        self,
        delegator_address: ChecksumAddress,
        *,
        w3: Optional[AsyncWeb3] = None,
    ) -> int:
        return await self._function_call(
            "getDelegatorTotalStakeAmount",
            delegatorAddress=delegator_address,
            w3=w3,
        )

    async def get_all_delegator_addresses(
        self, *, w3: Optional[AsyncWeb3] = None
    ) -> List[ChecksumAddress]:
        return await self._function_call(
            "getAllDelegatorAddresses",
            w3=w3,
        )

    async def get_all_node_addresses(
        self, *, w3: Optional[AsyncWeb3] = None
    ) -> List[ChecksumAddress]:
        return await self._function_call(
            "getAllNodeAddresses",
            w3=w3,
        )

