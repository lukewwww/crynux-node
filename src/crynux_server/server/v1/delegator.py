from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Body
from pydantic import BaseModel

from ..depends import ContractsDep
from .utils import CommonResponse

router = APIRouter(prefix="/delegator")


class SetDelegatorShareInput(BaseModel):
    share: int


@router.post("/share", response_model=CommonResponse)
async def set_delegator_share(
    input: Annotated[SetDelegatorShareInput, Body()],
    *,
    contracts: ContractsDep,
    background: BackgroundTasks,
):
    waiter = await contracts.user_staking_contract.set_delegator_share(input.share)
    background.add_task(waiter.wait)
    return CommonResponse()
