from anyio import to_thread
from fastapi import APIRouter
from pydantic import BaseModel

from crynux_server.config import get_staking_amount, set_staking_amount

from ..depends import ContractsDep
from .utils import CommonResponse

router = APIRouter(prefix="/settings")


class SettingsResponse(BaseModel):
    staking_amount: int


class MinStakingAmountResponse(BaseModel):
    min_staking_amount: str


@router.get("", response_model=SettingsResponse)
async def get_settings():
    staking_amount = get_staking_amount()
    return SettingsResponse(staking_amount=staking_amount)


@router.get("/min-staking-amount", response_model=MinStakingAmountResponse)
async def get_min_staking_amount(*, contracts: ContractsDep):
    min_staking_amount = await contracts.node_staking_contract.get_min_stake_amount()
    return MinStakingAmountResponse(min_staking_amount=str(min_staking_amount))


class SetSettingsInput(BaseModel):
    staking_amount: int


@router.post("", response_model=CommonResponse)
async def set_settings(input: SetSettingsInput):
    await to_thread.run_sync(set_staking_amount, input.staking_amount)
    return CommonResponse(success=True)
