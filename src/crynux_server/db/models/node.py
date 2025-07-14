import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from crynux_server.models import NodeStatus

from .base import Base, BaseMixin


class NodeState(Base, BaseMixin):
    __tablename__ = "node_states"

    status: Mapped[NodeStatus] = mapped_column(
        sa.Enum(NodeStatus), index=True, nullable=False
    )
    message: Mapped[str] = mapped_column(default="", index=False, nullable=False)
    init_message: Mapped[str] = mapped_column(default="", index=False, nullable=False)


class NodeScoreState(Base, BaseMixin):
    __tablename__ = "node_score_states"

    qos_score: Mapped[float] = mapped_column(default=0, index=False, nullable=False)
    staking_score: Mapped[float] = mapped_column(default=0, index=False, nullable=False)
    prob_weight: Mapped[float] = mapped_column(default=0, index=False, nullable=False)
