import logging
from contextlib import asynccontextmanager
from typing import List, Optional

from anyio import Lock, fail_after, get_cancelled_exc_class, sleep, CancelScope
from web3 import Web3

from crynux_server import models
from crynux_server.config import get_staking_amount
from crynux_server.contracts import Contracts, TxOption
from crynux_server.download_model_cache import DownloadModelCache
from crynux_server.relay.abc import Relay
from crynux_server.relay.exceptions import RelayError
from crynux_server.contracts.exceptions import TxRevertedError

from .state_cache import ManagerStateCache

_logger = logging.getLogger(__name__)


class NodeStateManager(object):
    def __init__(
        self,
        state_cache: ManagerStateCache,
        download_model_cache: DownloadModelCache,
        contracts: Contracts,
        relay: Relay,
    ):
        self.state_cache = state_cache
        self.download_model_cache = download_model_cache
        self.contracts = contracts
        self.relay = relay

        self._tx_lock = Lock()

        self._auto_unstake_scope = None
        self._sync_node_status_scope = None

    async def _get_node_status(self):
        node_info = await self.relay.node_get_node_info()
        remote_status = node_info.status
        local_status = models.convert_node_status(remote_status)
        return local_status

    async def _wait_for_running(self):
        local_status = await self._get_node_status()
        assert (
            local_status == models.NodeStatus.Running
        ), "Node status on chain is not running."
        await self.state_cache.set_node_state(local_status)
        await self.state_cache.set_tx_state(models.TxStatus.Success)

    async def _wait_for_stop(self):

        while True:
            local_status = await self._get_node_status()
            assert local_status in [
                models.NodeStatus.Stopped,
                models.NodeStatus.PendingStop,
            ], "Node status on chain is not stopped or pending."
            await self.state_cache.set_node_state(local_status)
            if local_status == models.NodeStatus.Stopped:
                node_staking_info = await self.contracts.node_staking_contract.get_staking_info(self.contracts.account)
                staking_amount = node_staking_info.staked_balance + node_staking_info.staked_credits
                if staking_amount > 0 and node_staking_info.is_locked:
                    waiter = await self.contracts.node_staking_contract.unstake()
                    await waiter.wait()
                await self.state_cache.set_tx_state(models.TxStatus.Success)
                return

    async def _wait_for_pause(self):
        pending = True

        while True:
            local_status = await self._get_node_status()
            assert local_status in [
                models.NodeStatus.Paused,
                models.NodeStatus.PendingPause,
            ], "Node status on chain is not paused or pending"
            await self.state_cache.set_node_state(local_status)
            if pending:
                await self.state_cache.set_tx_state(models.TxStatus.Success)
                pending = False
            if local_status == models.NodeStatus.Paused:
                break

    async def sync_node_status(self, interval: float = 5):
        assert self._sync_node_status_scope is None

        try:
            with CancelScope() as scope:
                self._sync_node_status_scope = scope
                while True:
                    node_info = await self.relay.node_get_node_info()
                    remote_status = node_info.status
                    local_status = models.convert_node_status(remote_status)
                    current_status = (await self.state_cache.get_node_state()).status
                    if local_status != current_status:
                        await self.state_cache.set_node_state(local_status)
                    node_score_state = models.NodeScoreState(
                        qos_score=node_info.qos_score,
                        staking_score=node_info.staking_score,
                        prob_weight=node_info.prob_weight,
                    )
                    await self.state_cache.set_node_score_state(node_score_state)
                    await sleep(interval)
        finally:
            self._sync_node_status_scope = None

    async def auto_unstake(self, interval: float = 5):
        assert self._auto_unstake_scope is None

        try:
            with CancelScope() as scope:
                self._auto_unstake_scope = scope
                while True:
                    node_status = (await self.state_cache.get_node_state()).status
                    tx_status = (await self.state_cache.get_tx_state()).status
                    if node_status == models.NodeStatus.Stopped and tx_status != models.TxStatus.Pending:
                        async with self._tx_lock:
                            node_status = (await self.state_cache.get_node_state()).status
                            tx_status = (await self.state_cache.get_tx_state()).status
                            if node_status == models.NodeStatus.Stopped and tx_status != models.TxStatus.Pending:
                                node_staking_info = await self.contracts.node_staking_contract.get_staking_info(self.contracts.account)
                                staking_amount = node_staking_info.staked_balance + node_staking_info.staked_credits
                                if staking_amount > 0 and node_staking_info.is_locked:
                                    await self.state_cache.set_tx_state(models.TxStatus.Pending)
                                    async with self._wrap_tx_error():
                                        waiter = await self.contracts.node_staking_contract.unstake()
                                        await waiter.wait()
                                        await self.state_cache.set_tx_state(models.TxStatus.Success)
                        
                    await sleep(interval)
        finally:
            self._auto_unstake_scope = None

    def stop_sync(self):
        if self._sync_node_status_scope is not None:
            self._sync_node_status_scope.cancel()

    def stop_auto_unstake(self):
        if self._auto_unstake_scope is not None:
            self._auto_unstake_scope.cancel()

    @asynccontextmanager
    async def _wrap_tx_error(self):
        try:
            yield
        except KeyboardInterrupt:
            raise
        except get_cancelled_exc_class():
            raise
        except (RelayError, AssertionError, ValueError, TxRevertedError) as e:
            _logger.error(f"tx error {str(e)}")
            with fail_after(5, shield=True):
                await self.state_cache.set_tx_state(models.TxStatus.Error, str(e))
            raise
        except Exception as e:
            _logger.exception(e)
            _logger.error("unknown tx error")
            raise

    async def try_start(
        self, gpu_name: str, gpu_vram: int, version: List[int], *, option: "Optional[TxOption]" = None
    ):
        _logger.info("Trying to join the network automatically...")
        while True:
            node_info = await self.relay.node_get_node_info()
            status = node_info.status
            if status in [
                models.ChainNodeStatus.AVAILABLE,
                models.ChainNodeStatus.BUSY,
                models.ChainNodeStatus.PENDING_PAUSE,
                models.ChainNodeStatus.PENDING_QUIT,
            ]:
                _logger.info("Node has joined in the network.")
                local_status = models.convert_node_status(status)
                await self.state_cache.set_node_state(local_status)
                break

            elif status == models.ChainNodeStatus.QUIT:
                staking_amount = Web3.to_wei(get_staking_amount(), "ether")
                balance = await self.contracts.get_balance(self.contracts.account)
                credits = await self.contracts.credits_contract.get_credits(self.contracts.account)
                total_balance = balance + credits
                if total_balance < staking_amount + Web3.to_wei(0.001, "ether"):
                    raise ValueError("Node token balance is not enough to join")
                
                if credits < staking_amount:
                    staked_credits = credits
                    staked_balance = staking_amount - credits
                else:
                    staked_credits = staking_amount
                    staked_balance = 0

                tx_status = (await self.state_cache.get_tx_state()).status
                if tx_status == models.TxStatus.Pending:
                    continue

                async with self._tx_lock:
                    tx_status = (await self.state_cache.get_tx_state()).status
                    if tx_status == models.TxStatus.Pending:
                        continue
                    await self.state_cache.set_tx_state(models.TxStatus.Pending)
                    async with self._wrap_tx_error():
                        waiter = await self.contracts.node_staking_contract.stake(staked_balance, staked_credits, option=option)
                        await waiter.wait()

                        download_models = await self.download_model_cache.load_all()
                        model_ids = [model.model.to_model_id() for model in download_models]
                        await self.relay.node_join(
                            gpu_name=gpu_name,
                            gpu_vram=gpu_vram,
                            version=".".join(str(v) for v in version),
                            model_ids=model_ids,
                            staking_amount=staking_amount,
                        )
                        # update tx state to avoid the web user controlling node status by api
                        # it's the same in try_stop method
                        await self._wait_for_running()
            elif status == models.ChainNodeStatus.PAUSED:
                tx_status = (await self.state_cache.get_tx_state()).status
                if tx_status == models.TxStatus.Pending:
                    continue

                async with self._tx_lock:
                    tx_status = (await self.state_cache.get_tx_state()).status
                    if tx_status == models.TxStatus.Pending:
                        continue
                    await self.state_cache.set_tx_state(models.TxStatus.Pending)
                    async with self._wrap_tx_error():
                        await self.relay.node_resume()
                        await self._wait_for_running()

            _logger.info("Node joins in the network successfully.")
            break

    async def try_stop(self, *, option: "Optional[TxOption]" = None):
        while True:
            node_info = await self.relay.node_get_node_info()
            status = node_info.status
            
            if status == models.ChainNodeStatus.AVAILABLE:
                tx_status = (await self.state_cache.get_tx_state()).status
                if tx_status == models.TxStatus.Pending:
                    continue
                async with self._tx_lock:
                    tx_status = (await self.state_cache.get_tx_state()).status
                    if tx_status == models.TxStatus.Pending:
                        continue
                    await self.state_cache.set_tx_state(models.TxStatus.Pending)
                    async with self._wrap_tx_error():
                        await self.relay.node_quit()
                        await self._wait_for_stop()
                _logger.info("Node leaves the network successfully.")
            elif status == models.ChainNodeStatus.QUIT:
                _logger.info("Node has already left the network.")
            else:
                _logger.info(
                    f"Node status is {models.convert_node_status(status)}, cannot leave the network automatically"
                )
            
            return

    async def start(
        self,
        gpu_name: str,
        gpu_vram: int,
        version: List[int],
        *,
        option: "Optional[TxOption]" = None,
    ):
        node_status = (await self.state_cache.get_node_state()).status
        assert (
            node_status == models.NodeStatus.Stopped
        ), "Cannot start node. Node is not stopped."
        tx_status = (await self.state_cache.get_tx_state()).status
        assert (
            tx_status != models.TxStatus.Pending
        ), "Cannot start node. Last transaction is in pending."

        async with self._tx_lock:
            node_status = (await self.state_cache.get_node_state()).status
            assert (
                node_status == models.NodeStatus.Stopped
            ), "Cannot start node. Node is not stopped."
            tx_status = (await self.state_cache.get_tx_state()).status
            assert (
                tx_status != models.TxStatus.Pending
            ), "Cannot start node. Last transaction is in pending."
            await self.state_cache.set_tx_state(models.TxStatus.Pending)

            node_staking_info = await self.contracts.node_staking_contract.get_staking_info(self.contracts.account)
            current_staking_amount = node_staking_info.staked_balance + node_staking_info.staked_credits
            assert current_staking_amount == 0, "Node is already staked"

            staking_amount = Web3.to_wei(get_staking_amount(), "ether")
            balance = await self.contracts.get_balance(self.contracts.account)
            credits = await self.contracts.credits_contract.get_credits(self.contracts.account)
            total_balance = balance + credits
            if total_balance < staking_amount + Web3.to_wei(0.001, "ether"):
                raise ValueError("Node token balance is not enough to join")
            
            if credits < staking_amount:
                staked_credits = credits
                staked_balance = staking_amount - credits
            else:
                staked_credits = staking_amount
                staked_balance = 0
                
            async with self._wrap_tx_error():
                waiter = await self.contracts.node_staking_contract.stake(staked_balance, staked_credits, option=option)

                async def wait():
                    async with self._tx_lock:
                        async with self._wrap_tx_error():
                            await waiter.wait()

                            download_models = await self.download_model_cache.load_all()
                            model_ids = [model.model.to_model_id() for model in download_models]
                            await self.relay.node_join(
                                gpu_name=gpu_name,
                                gpu_vram=gpu_vram,
                                model_ids=model_ids,
                                version=".".join(str(v) for v in version),
                                staking_amount=staking_amount,
                            )
                            await self._wait_for_running()

                return wait

    async def stop(
        self,
        *,
        option: "Optional[TxOption]" = None,
    ):
        node_status = (await self.state_cache.get_node_state()).status
        assert (
            node_status == models.NodeStatus.Running
        ), "Cannot stop node. Node is not running."
        tx_status = (await self.state_cache.get_tx_state()).status
        assert (
            tx_status != models.TxStatus.Pending
        ), "Cannot start node. Last transaction is in pending."
        async with self._tx_lock:
            node_status = (await self.state_cache.get_node_state()).status
            assert (
                node_status == models.NodeStatus.Running
            ), "Cannot stop node. Node is not running."
            tx_status = (await self.state_cache.get_tx_state()).status
            assert (
                tx_status != models.TxStatus.Pending
            ), "Cannot start node. Last transaction is in pending."

            await self.state_cache.set_tx_state(models.TxStatus.Pending)

            async with self._wrap_tx_error():

                await self.relay.node_quit()

            async def wait():
                async with self._tx_lock:
                    async with self._wrap_tx_error():
                        await self._wait_for_stop()

            return wait

    async def pause(
        self,
        *,
        option: "Optional[TxOption]" = None,
    ):
        node_status = (await self.state_cache.get_node_state()).status
        assert (
            node_status == models.NodeStatus.Running
        ), "Cannot stop node. Node is not running."
        tx_status = (await self.state_cache.get_tx_state()).status
        assert (
            tx_status != models.TxStatus.Pending
        ), "Cannot start node. Last transaction is in pending."
        async with self._tx_lock:
            node_status = (await self.state_cache.get_node_state()).status
            assert (
                node_status == models.NodeStatus.Running
            ), "Cannot stop node. Node is not running."
            tx_status = (await self.state_cache.get_tx_state()).status
            assert (
                tx_status != models.TxStatus.Pending
            ), "Cannot start node. Last transaction is in pending."

            await self.state_cache.set_tx_state(models.TxStatus.Pending)

            async with self._wrap_tx_error():
                await self.relay.node_pause()

                async def wait():
                    async with self._tx_lock:
                        async with self._wrap_tx_error():
                            await self._wait_for_pause()

                return wait

    async def resume(
        self,
        *,
        option: "Optional[TxOption]" = None,
    ):
        node_status = (await self.state_cache.get_node_state()).status
        assert (
            node_status == models.NodeStatus.Paused
        ), "Cannot stop node. Node is not running."
        tx_status = (await self.state_cache.get_tx_state()).status
        assert (
            tx_status != models.TxStatus.Pending
        ), "Cannot start node. Last transaction is in pending."
        async with self._tx_lock:
            node_status = (await self.state_cache.get_node_state()).status
            assert (
                node_status == models.NodeStatus.Paused
            ), "Cannot stop node. Node is not running."
            tx_status = (await self.state_cache.get_tx_state()).status
            assert (
                tx_status != models.TxStatus.Pending
            ), "Cannot start node. Last transaction is in pending."
            await self.state_cache.set_tx_state(models.TxStatus.Pending)

            async with self._wrap_tx_error():
                await self.relay.node_resume()

            async def wait():
                async with self._tx_lock:
                    async with self._wrap_tx_error():
                        await self._wait_for_running()

            return wait


_default_state_manager: Optional[NodeStateManager] = None


def get_node_state_manager() -> NodeStateManager:
    assert _default_state_manager is not None, "NodeStateManager has not been set."

    return _default_state_manager


def set_node_state_manager(manager: NodeStateManager):
    global _default_state_manager

    _default_state_manager = manager
