# will test on real life chain
# just one test as example
import time
from brownie import network
import pytest
from scripts.deploy import deploy_lottery

from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    fund_with_link,
    get_account,
)

# run this on --network rinkeby
def test_can_pick_winner():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:  # now only network
        pytest.skip()
    lottery = deploy_lottery()
    print(f"Lottery address is {lottery.address}")
    account = get_account()
    print(f"Account address is {account}")
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()}) #entered twice with same account
    fund_with_link(lottery)
    starting_balance_account = account.balance()
    balance_of_lottery_1 = lottery.balance()

    tx = lottery.endLottery({"from": account})
    tx.wait(1)
    # now a bit different. interegration me we dont pretend that we are chainlink node
    time.sleep(180)
    balance_of_lottery_2 = lottery.balance()
    print(f"Starting balance: {account.balance()}")
    print("----------------------------------------------")
    print(f"Lottery balance before ending it: {balance_of_lottery_1}")
    print("----------------------------------------------")
    print(
        f"Lottery balance after ending it (should be 0 ideally): {balance_of_lottery_2}"
    )
    print("----------------------------------------------")
    print(lottery.recentWinner())
    assert lottery.recentWinner() == account
    assert lottery.balance() == 0
