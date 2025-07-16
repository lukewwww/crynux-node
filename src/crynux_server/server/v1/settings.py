from anyio import to_thread
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from crynux_server.config import get_staking_amount, set_staking_amount
from crynux_server.models import NodeStatus

from ..depends import ManagerStateCacheDep
from .utils import CommonResponse

router = APIRouter(prefix="/settings")


class SettingsResponse(BaseModel):
    staking_amount: int


@router.get("", response_model=SettingsResponse)
async def get_settings():
    staking_amount = get_staking_amount()
    return SettingsResponse(staking_amount=staking_amount)


class SetSettingsInput(BaseModel):
    staking_amount: int = Field(..., ge=1)


@router.post("", response_model=CommonResponse)
async def set_settings(input: SetSettingsInput, *, state_manager: ManagerStateCacheDep):
    node_state = await state_manager.get_node_state()
    if node_state.status != NodeStatus.Stopped and node_state.status != NodeStatus.Init:
        raise HTTPException(
            status_code=400, detail="Node is not stopped or initializing"
        )

    await to_thread.run_sync(set_staking_amount, input.staking_amount)
    return CommonResponse(success=True)
