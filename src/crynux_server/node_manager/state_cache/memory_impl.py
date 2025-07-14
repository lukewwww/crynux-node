from crynux_server.models import (NodeScoreState, NodeState, NodeStatus,
                                  TxState, TxStatus)
from crynux_server.models.tx import TxState

from .abc import StateCache


class MemoryNodeStateCache(StateCache[NodeState]):
    def __init__(self) -> None:
        self._state = NodeState(status=NodeStatus.Init)

    async def get(self) -> NodeState:
        return self._state

    async def set(self, state: NodeState):
        self._state = state


class MemoryTxStateCache(StateCache[TxState]):
    def __init__(self) -> None:
        self._state = TxState(status=TxStatus.Success)

    async def get(self) -> TxState:
        return self._state

    async def set(self, state: TxState):
        self._state = state


class MemoryNodeScoreStateCache(StateCache[NodeScoreState]):
    def __init__(self) -> None:
        self._state = NodeScoreState(qos_score=0, staking_score=0, prob_weight=0)

    async def get(self) -> NodeScoreState:
        return self._state

    async def set(self, state: NodeScoreState):
        self._state = state
