from anyio import to_thread
from fastapi import APIRouter
from pydantic import BaseModel, Field

from crynux_server.config import get_staking_amount, set_staking_amount

from .utils import CommonResponse

router = APIRouter(prefix="/settings")


class SettingsResponse(BaseModel):
    staking_amount: int


@router.get("", response_model=SettingsResponse)
async def get_settings():
    staking_amount = get_staking_amount()
    return SettingsResponse(staking_amount=staking_amount)


class SetSettingsInput(BaseModel):
    staking_amount: int = Field(..., ge=400)


@router.post("", response_model=CommonResponse)
async def set_settings(input: SetSettingsInput):
    await to_thread.run_sync(set_staking_amount, input.staking_amount)
    return CommonResponse(success=True)
