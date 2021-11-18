from brownie import Lottery, network, config
from scripts.helpful_scripts import get_account, get_contract, fund_with_link
import time


def deploy_lottery():
    account = get_account()
    # can pass parameter as get_account(id="fcc-account")
    # Lottery constructor:
    #     address _priceFeed, -chainlink aggregatorv3interface
    #     address _vrfCoordinator, -the vrf random number address
    #     address _link, -account that holds link i think
    #     uint256 _fee, -amount of link to be paid?
    #     bytes32 _keyhash -idk

    # pricefeed adrress either from 1) deploy a mock and get its .address or 2) direct from config file
    # so here what is being done is; you get the address by actually deploying the mock of the contract if we are on local
    # or deploying the contract if we are on some test network
    lottery = Lottery.deploy(
        get_contract("eth_usd_price_feed").address,
        get_contract("vrf_coordinator").address,
        get_contract("link_token").address,
        config["networks"][network.show_active()]["fee"],
        config["networks"][network.show_active()]["keyhash"],
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify", False),
    )
    # verify value if present, if not then send False
    print("Deployed lottery!!")
    return lottery  # useful in testing


# deploying to testnet takes a while, so might as well have some additional functionality before deploying no?


def start_lottery():
    account = get_account()
    lottery = Lottery[-1]
    start_txn = lottery.startLottery({"from": account})
    # remember u want to wait for last txn to go through
    start_txn.wait(1)
    print("Lottery started!!")


def enter_lottery():
    account = get_account()
    lottery = Lottery[-1]
    # need to pick entrance value
    value = (
        lottery.getEntranceFee() + 100000
    )  # add a bit of wei; not a reference txn so no need for "from"
    txn = lottery.enter(
        {"from": account, "value": value}
    )  # remember this!! gotta pass value as parameter
    txn.wait(1)
    print(account)
    print(value)
    print(f"Lottery entered successfully by {account.address}")


# now before we end the lottery we actually need some LINK in the contract
def end_lottery():
    account = get_account()
    print("Account we have here is")
    print(account)
    lottery = Lottery[-1]
    # funding the contract with LINK goes in helpful_scripts
    tx = fund_with_link(lottery.address)
    tx.wait(1)
    ending_transaction = lottery.endLottery({"from": account})
    ending_transaction.wait(1)
    # now we are waiting for a callback
    time.sleep(100)
    # chainlink node responds within few blocks typically
    # print(f"The state of lottery is {lottery.lottery_state()}")
    print(
        lottery.recentWinner()
    )  # remember there is a function() kind of thing for public variable, it's getter()
    # but for ganache - no local node! How will a chainlink node respond?? it returns 00


def main():
    deploy_lottery()
    start_lottery()
    enter_lottery()
    end_lottery()
