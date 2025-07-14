import sqlalchemy as sa

from crynux_server import db
from crynux_server.models import (NodeScoreState, NodeState, NodeStatus,
                                  TxState, TxStatus)
from crynux_server.models.tx import TxState

from .abc import StateCache


class DbNodeStateCache(StateCache[NodeState]):
    async def get(self) -> NodeState:
        async with db.session_scope() as sess:
            q = sa.select(db.models.NodeState).where(db.models.NodeState.id == 1)
            state = (await sess.execute(q)).scalar_one_or_none()
            if state is None:
                return NodeState(status=NodeStatus.Init)
            else:
                return NodeState(
                    status=state.status,
                    message=state.message,
                    init_message=state.init_message,
                )

    async def set(self, state: NodeState):
        async with db.session_scope() as sess:
            q = sa.select(db.models.NodeState).where(db.models.NodeState.id == 1)
            db_state = (await sess.execute(q)).scalar_one_or_none()
            if db_state is None:
                db_state = db.models.NodeState(
                    status=state.status,
                    message=state.message,
                    init_message=state.init_message,
                )
                sess.add(db_state)
            else:
                db_state.status = state.status
                db_state.message = state.message
                db_state.init_message = state.init_message
            await sess.commit()


class DbTxStateCache(StateCache[TxState]):
    async def get(self) -> TxState:
        async with db.session_scope() as sess:
            q = sa.select(db.models.TxState).where(db.models.TxState.id == 1)
            state = (await sess.execute(q)).scalar_one_or_none()
            if state is None:
                return TxState(status=TxStatus.Success)
            else:
                return TxState(status=state.status, error=state.error)

    async def set(self, state: TxState):
        async with db.session_scope() as sess:
            q = sa.select(db.models.TxState).where(db.models.TxState.id == 1)
            db_state = (await sess.execute(q)).scalar_one_or_none()
            if db_state is None:
                db_state = db.models.TxState(status=state.status, error=state.error)
                sess.add(db_state)
            else:
                db_state.status = state.status
                db_state.error = state.error
            await sess.commit()

class DbNodeScoreStateCache(StateCache[NodeScoreState]):
    async def get(self) -> NodeScoreState:
        async with db.session_scope() as sess:
            q = sa.select(db.models.NodeScoreState).where(db.models.NodeScoreState.id == 1)
            state = (await sess.execute(q)).scalar_one_or_none()
            if state is None:
                return NodeScoreState(qos_score=0, staking_score=0, prob_weight=0)
            else:
                return NodeScoreState(qos_score=state.qos_score, staking_score=state.staking_score, prob_weight=state.prob_weight)

    async def set(self, state: NodeScoreState):
        async with db.session_scope() as sess:
            q = sa.select(db.models.NodeScoreState).where(db.models.NodeScoreState.id == 1)
            db_state = (await sess.execute(q)).scalar_one_or_none()
            if db_state is None:
                db_state = db.models.NodeScoreState(qos_score=state.qos_score, staking_score=state.staking_score, prob_weight=state.prob_weight)
                sess.add(db_state)
            else:
                db_state.qos_score = state.qos_score
                db_state.staking_score = state.staking_score
                db_state.prob_weight = state.prob_weight
            await sess.commit()