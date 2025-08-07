import logging

from anyio import create_task_group, get_cancelled_exc_class, sleep, ExceptionGroup
from pydantic import BaseModel

from crynux_server.config import wait_privkey
from crynux_server.relay import get_relay
from crynux_server.utils import get_address_from_privkey

_logger = logging.getLogger(__name__)


class AccountInfo(BaseModel):
    address: str
    balance: str
    staking: str


_account_info = AccountInfo(address="", balance="0", staking="0")


async def update_account_info(interval: int):
    privkey = await wait_privkey()
    _account_info.address = get_address_from_privkey(privkey)

    while True:
        try:
            relay = get_relay()

            async def _update_balance():
                _account_info.balance = str(await relay.get_balance())
                _logger.debug(f"balance: {_account_info.balance}")

            async def _update_staking():
                _account_info.staking = str(await relay.get_staking_amount())
                _logger.debug(f"staking: {_account_info.staking}")

            async with create_task_group() as tg:
                tg.start_soon(_update_balance)
                tg.start_soon(_update_staking)
        except AssertionError:
            pass
        except get_cancelled_exc_class():
            _logger.debug("update account info cancelled")
            raise
        except Exception as e:
            _logger.error("update account info error")
            _logger.exception(e)
        except ExceptionGroup as e:
            _logger.error("update account info error")
            _logger.exception(e)
        await sleep(interval)


def get_account_info():
    return _account_info
