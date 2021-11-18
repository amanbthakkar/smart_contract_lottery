from brownie import (
    accounts,
    network,
    config,
    MockV3Aggregator,
    Contract,
    VRFCoordinatorMock,
    LinkToken,
    interface,
)


FORKED_LOCAL_ENVIRONMENTS = ["mainnet-fork"]
LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "ganache-local"]

DECIMALS = 8
STARTING_PRICE = 400000000000

# remember there were 3 ways for account loading
# 1. accounts[0]
# 2. accounts.add()

# 3. is actually accounts.load("id") ----> these were set from command line remember? lets modify function to allow this


def get_account(index=None, id=None):
    # if we pass an index, means we use an index from the accounts[i], and if we pass id we use the predefined "fcc-account"
    # that can be checked by running brownie accounts list
    if index:
        return accounts[index]
    if id:
        return accounts.load(id)
    if (
        network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS
        or network.show_active() in FORKED_LOCAL_ENVIRONMENTS
    ):
        return accounts[0]
    return accounts.add(config["wallets"]["from_key"])


contract_to_mock = {
    "eth_usd_price_feed": MockV3Aggregator,
    "vrf_coordinator": VRFCoordinatorMock,
    "link_token": LinkToken,
}  # mapping


def deploy_mocks(decimals=DECIMALS, starting_price=STARTING_PRICE):
    account = get_account()
    print(f"Active network is {network.show_active()}")
    print("Deploying mocks...")
    MockV3Aggregator.deploy(decimals, starting_price, {"from": account})
    link_token = LinkToken.deploy({"from": account})
    VRFCoordinatorMock.deploy(link_token.address, {"from": account})
    print("Deployed!")


def get_contract(contract_name):
    # this is the "pricefeed" contract
    # if not on local, we fetched from config
    # if on local, we deployed a mock
    # then we return it
    """This function will grab the contract addresses from the brownie config if defined else will deploy a mock and return it
    Args: contract name (string)
    return: a contract (a brownie.network.contract.ProjectContract) - most recent version of the contract
    """
    contract_type = contract_to_mock[contract_name]
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        if len(contract_type) <= 0:
            deploy_mocks()
        contract = contract_type[-1]
    else:
        # if testnets
        contract_address = config["networks"][network.show_active()][contract_name]
        # yeah direct pricefeed
        # now similar to above we actually create the contract from abi (which we already have from the MockV3Aggregator)
        # need to import Contract from brownie for this, and _name returns the name
        contract = Contract.from_abi(
            contract_type._name, contract_address, contract_type.abi
        )
        print(
            f"Just to check: 1) is contract_address and 2) is deployed contract's address. (if same could have returned address) {contract_type._name}"
        )
        print(f"1. {contract_address}")
        print(f"2. {contract.address}")
    return contract


def fund_with_link(
    contract_address, account=None, link_token=None, amount=100000000000000000
):  # 0.1ETH
    account = (
        account if account else get_account()
    )  # will return actual account if rinkeby
    link_token = (
        link_token if link_token else get_contract("link_token")
    )  # will return actual link address if rinkeby
    # tx = link_token.transfer(contract_address, amount, {"from": account})
    # tx.wait(1)
    # can also use interfaces instead of mock link token contract
    # what if u only have interface?
    # add linktokenInterface
    link_token_contract = interface.LinkTokenInterface(
        link_token.address
    )  # another way to create a contract instead of abi/mock and all
    tx = link_token_contract.transfer(contract_address, amount, {"from": account})
    tx.wait(1)
    print("Funded contract")
    return tx
