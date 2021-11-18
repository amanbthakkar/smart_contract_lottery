1. Users enter lottery with ETH
2. Admin will choose lottery end time (not exactly decentralized but decentralized enough imo)
3. Lottery will select a random winner based on a random number obtained from ChainLink

Stuff used:

- Deploying mocks locally and on rinkeby
- MockAggregatorV3 and LinkToken
- Using ChainLink's VRF to get a random number using the request/response thingy which doesn't respond immediately but uses an overriden callback instead
- Seperation of testing into unit & integration
- skipped the part about verifying rinkeby deployed contracts (for now)
- deploying a contract using 1) abi and 2) directly from interfaces
