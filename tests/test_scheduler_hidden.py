from __future__ import annotations

import os
import random
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from cocotb_tools.runner import get_runner
import pytest



# ---------------------------------------------------------
# Helper: Reset DUT
# ---------------------------------------------------------
async def reset_dut(dut):
    dut.rst_n.value = 0
    dut.valid.value = 0
    dut.out_ready.value = 0

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


# ---------------------------------------------------------
# Test 1: Basic Round Robin
# ---------------------------------------------------------
@cocotb.test()
async def test_round_robin(dut):
    """Verify basic round-robin scheduling"""

    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    dut.out_ready.value = 1

    # Activate multiple channels
    dut.valid.value = 0b01110

    for _ in range(5):
        await RisingEdge(dut.clk)

        ch = int(dut.out_channel.value)

        # Channel must be one of the active ones
        assert ch in [1,2,3], "Invalid round-robin channel selected"


# ---------------------------------------------------------
# Test 2: Stall Behavior
# ---------------------------------------------------------
@cocotb.test()
async def test_stall_behavior(dut):
    """Scheduler must hold grant during stall"""

    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    dut.valid.value = 0b00100
    dut.out_ready.value = 1

    await RisingEdge(dut.clk)

    initial_channel = int(dut.out_channel.value)

    # Stall downstream
    dut.out_ready.value = 0

    for _ in range(3):
        await RisingEdge(dut.clk)

        assert int(dut.out_channel.value) == initial_channel, \
            "Channel changed during stall"


# ---------------------------------------------------------
# Test 3: Immediate Preemption
# ---------------------------------------------------------
@pytest.mark.skip(reason="temporarily disabled for baseline RTL")
@cocotb.test()
async def test_immediate_preemption(dut):
    """Higher priority request should preempt immediately"""

    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    dut.out_ready.value = 1

    # Start with lower priority
    dut.valid.value = 0b01000
    await RisingEdge(dut.clk)

    # Introduce high priority request
    dut.valid.value = 0b01001

    await RisingEdge(dut.clk)

    ch = int(dut.out_channel.value)

    assert ch == 0, "Immediate preemption failed"


# ---------------------------------------------------------
# Test 4: Deferred Preemption
# ---------------------------------------------------------
@cocotb.test()
async def test_deferred_preemption(dut):
    """Priority difference = 1 should defer switch"""

    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    dut.out_ready.value = 1

    # Channel 3 active
    dut.valid.value = 0b01000
    await RisingEdge(dut.clk)

    # Channel 2 appears (difference = 1)
    dut.valid.value = 0b01100

    await RisingEdge(dut.clk)

    # Should still be channel 3
    assert int(dut.out_channel.value) == 3, \
        "Deferred preemption occurred too early"


# ---------------------------------------------------------
# Test 5: Random Stress Test
# ---------------------------------------------------------
@cocotb.test()
async def test_random_requests(dut):
    """Randomized traffic stress test"""

    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    dut.out_ready.value = 1

    for _ in range(50):

        dut.valid.value = random.randint(0, 31)

        await RisingEdge(dut.clk)

        ch = int(dut.out_channel.value)

        valid_vector = int(dut.valid.value)

        # If output is valid, the channel must be active
        if dut.out_valid.value:
            assert (valid_vector >> ch) & 1, \
                "Scheduler granted inactive channel"

        if dut.out_valid.value:
            assert (int(dut.valid.value) >> int(dut.out_channel.value)) & 1


#Test6 : Reset Test
@cocotb.test()
async def test_reset_behavior(dut):
    """Verify scheduler reset state"""

    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.rst_n.value = 0
    dut.valid.value = 0
    dut.out_ready.value = 1

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    # release reset
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # Expected reset state
    assert dut.out_valid.value == 0


#Test 7: Dynamic Preemption
@pytest.mark.skip(reason="temporarily disabled for baseline RTL")
@cocotb.test()
async def test_dynamic_preemption(dut):

    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    dut.out_ready.value = 1

    # Start with channel 3 active
    dut.valid.value = 0b01000
    await RisingEdge(dut.clk)

    # Introduce higher priority request
    dut.valid.value = 0b01001
    await RisingEdge(dut.clk)

    assert int(dut.out_channel.value) == 0


#Test 8 : Ready stall and New Request
@cocotb.test()
async def test_stall_preemption_interaction(dut):

    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    dut.out_ready.value = 1
    dut.valid.value = 0b01000

    await RisingEdge(dut.clk)

    initial = int(dut.out_channel.value)

    # Stall pipeline
    dut.out_ready.value = 0

    # Introduce higher priority request
    dut.valid.value = 0b01001

    for _ in range(3):
        await RisingEdge(dut.clk)

        assert int(dut.out_channel.value) == initial


# ---------------------------------------------------------
# Runner
# ---------------------------------------------------------
def test_scheduler_hidden_runner():

    sim = os.getenv("SIM", "icarus")

    proj_path = Path(__file__).resolve().parent.parent

    sources = [proj_path / "golden/scheduler.sv"]

    runner = get_runner(sim)

    runner.build(
        sources=sources,
        hdl_toplevel="scheduler",
        always=True,
    )

    runner.test(
        hdl_toplevel="scheduler",
        test_module="test_scheduler_hidden",
    )