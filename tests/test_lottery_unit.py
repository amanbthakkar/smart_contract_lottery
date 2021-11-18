from brownie import Lottery, config, accounts, network, exceptions
from brownie.project.main import get_loaded_projects
from web3 import Web3
from scripts.deploy import deploy_lottery
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    fund_with_link,
    get_contract,
)
import pytest

"""
-----old one before all code improvements-----
def test_entrance_fee():
    account = accounts[0]
    lottery = Lottery.deploy(
        config["networks"][network.show_active()]["eth_usd_address"],
        {"from": account},
    )
    print("Lottery contract deployed!")
    print("Getting entry price in ETH...")
    eth_price = lottery.getEntranceFee()
    print(f"Current value of 50USD is {eth_price}")
    assert eth_price > Web3.toWei(0.009, "ether")
    assert eth_price < Web3.toWei(0.11, "ether")
"""


def test_get_entrance_fee():
    # only run this test on local development env
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # arrange
    lottery = deploy_lottery()
    # act
    entrance_fee = lottery.getEntranceFee()
    # test
    # if 2000eth/usd (because mock) then
    expected_fee = Web3.toWei((50 / 2000), "ether")
    assert expected_fee == entrance_fee
    # run with brownie test -k test_get_entrance_fee --network rinkeby will skip it!


def test_enter_started():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # arrange
    lottery = deploy_lottery()
    # now we need to see if anyone can enter without starting so just try to call the function
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter({"from": get_account(), "value": lottery.getEntranceFee()})


def test_can_start_and_enter():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    lottery = deploy_lottery()
    tx = lottery.startLottery({"from": account})
    tx.wait(1)
    txn = lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    txn.wait(1)
    assert lottery.players(0) == account


def test_can_end_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    lottery = deploy_lottery()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    # now to test we have to indeed send some link token
    fund_with_link(lottery)
    lottery.endLottery({"from": account})
    assert lottery.lottery_state() == 2


def test_can_correctly_choose_winner():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    lottery = deploy_lottery()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=1), "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=2), "value": lottery.getEntranceFee()})
    fund_with_link(lottery)
    # now to actually test everything, we gotta test the fulfillRandomness()
    # but that function is called by the chainlink node right, while returning a random number?
    # if u go to the vrfcoordinator mock, there is a callBackWithRandomness
    # this function actually has the v.rawFulfillRandomness.selector, which will eventually call the fulfillRandomness fn
    # so we gotta pretend to be a chainlink node to call this function, which will in turn eventually call our lottery's fulfillRandomness
    # for that we need the requestId (along with 2 more parameters)
    # so we emit an event (print line of blockchain) => now calling will emit an event
    account1 = get_account(index=1)
    starting_balance_account = account1.balance()
    balance_of_lottery_1 = lottery.balance()
    transaction = lottery.endLottery({"from": account})
    transaction.wait(1)
    # now we can look inside this transaction
    request_id = transaction.events["RequestedRandomness"]["requestId"]
    # now we use the callbackWithRandomness
    STATIC_RNG = 778  # any random number to be passed
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, STATIC_RNG, lottery.address, {"from": account}
    )
    balance_of_lottery_2 = lottery.balance()  # after fulfillrandomness is called
    print("----------------------------------------------")
    print(f"Request ID: {request_id}")
    print("----------------------------------------------")
    print(f"Starting balance: {account1.balance()}")
    print("----------------------------------------------")
    print(f"Lottery balance before ending it: {balance_of_lottery_1}")
    print("----------------------------------------------")
    print(
        f"Lottery balance after end it and distributing funds: {balance_of_lottery_2}"
    )
    print("----------------------------------------------")

    # now we are dummying responses from chainlink node
    # 777 % 3 = 0 i.e. first account is winner, and 2nd is 778

    # new balance = old balance + balance of lottery before ending it
    assert lottery.recentWinner() == get_account(index=1)
    assert lottery.balance() == 0
    assert account1.balance() == starting_balance_account + balance_of_lottery_1


# unit test is the way to integrate small pieces of node in the system - local network
# we want to do integration also - but this is on testnet, see on etherscan and all
# create 2 folders in test folder (unit and integration) ->
