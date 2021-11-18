//SPDX-License-Identifier: MIT
pragma solidity ^0.6.6;

import "@chainlink/contracts/src/v0.6/interfaces/AggregatorV3Interface.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@chainlink/contracts/src/v0.6/VRFConsumerBase.sol";

contract Lottery is VRFConsumerBase, Ownable {
    AggregatorV3Interface internal priceFeed;
    address payable[] public players;
    uint256 public usdEntryFee;

    //openzeppelin, inheritence
    //first start by thinking of what functions will be there
    //enter (the contract) - take money and enter the lottery
    //query price?
    //some creator will be able to start the lottery and end the lottery
    //will need to get chainlink aggregator price - that will come in dependencies
    //and then also gotta import chainlink price feed
    //might also want to import the safemath package if required
    //constructor will be able to get the pricefeed passed as a parameter

    //enums are a good way to create user defined objects kinda
    //their values are related to int values like 0,1,2,3...
    //hence they are good at representing "State" or "actions"
    //here we have states like - not started, ongoing, ended etc so enums could be useful

    enum LOTTERY_STATE {
        OPEN,
        CLOSED,
        CALCULATING_WINNER
    } //represented by 0,1,2
    event RequestedRandomness(bytes32 requestId);
    event SomeoneWon(uint256 _randomness);

    LOTTERY_STATE public lottery_state;
    uint256 public fee; //has to be public
    bytes32 public keyhash; //to identify chainlink vrf node
    address payable public recentWinner; //winner
    uint256 public randomness;

    //turns out you can define another constructor inside main one (i.e. define constructor of what you have inherited)
    //now the VRF constructor takes 2 params - VRF coordinator and LINK token, but also the code takes
    //whatever constructor is taking in is parameterized
    //remember we are sending the vrf coordinator, check deploy script for details

    constructor(
        address _priceFeed,
        address _vrfCoordinator,
        address _link,
        uint256 _fee,
        bytes32 _keyhash
    ) public VRFConsumerBase(_vrfCoordinator, _link) {
        //the $50 fee minimum is set right when the contract is deployed
        usdEntryFee = 50 * 10**18;
        priceFeed = AggregatorV3Interface(_priceFeed); //we get the value from deploy time rather than hard coding it
        lottery_state = LOTTERY_STATE.CLOSED; //or lottery_state = 1;
        fee = _fee;
        keyhash = _keyhash;
    }

    function enter() public payable {
        require(lottery_state == LOTTERY_STATE.OPEN);
        require(msg.value >= getEntranceFee(), "Not enough ETH!"); //dont enter if insufficient funds
        players.push(msg.sender);
    }

    function getEntranceFee() public view returns (uint256) {
        (, int256 price, , , ) = priceFeed.latestRoundData();
        uint256 adjustedPrice = uint256(price) * 10**10; //this has 18 decimal places
        uint256 costToEnter = (usdEntryFee * 10**18) / adjustedPrice;
        return costToEnter;
    }

    function startLottery() public onlyOwner {
        //gotta use onlyOwner modifier - could write our own or use OpenZeppelin
        //has to be closed rn
        require(
            lottery_state == LOTTERY_STATE.CLOSED,
            "Can't start a new one yet!"
        );
        lottery_state = LOTTERY_STATE.OPEN;
    }

    function endLottery() public onlyOwner {
        //randomness
        //bunching a bunch of data like {nonce, block.timestamp, block.difficulty and msg.sender} and keccack256 hashing it is a bad idea
        //these values are {predictable, predictable, manipulatable, predictible} => and keccak is always the same
        //so overall not v v secure even though its onlyOwner (as in not a good practice)
        //best is ChainLinks's VRF => VerifiableRandomFunction or something
        //uses some cryptography to make sure a number returned by the chainlink node is truly random

        require(lottery_state == LOTTERY_STATE.OPEN);
        lottery_state = LOTTERY_STATE.CALCULATING_WINNER;

        //generate a random number
        //chainlink vrf has a request response type thing
        //first you send a request
        //then after sometime they themselves send a response
        //you have to override that function to get the response
        //https://docs.chain.link/docs/get-a-random-number/
        //along with ETH gas fee, you also have to deposit some LINK tokens to the contract first
        //this LINK is payment for the random number generation service that they provide

        //how to request the random number? as per documentation there is a "return requestRandomness();"
        //on checking code on github, its a builtin fn that takes keyhash and fee and returns requestid

        bytes32 requestId = requestRandomness(keyhash, fee); //this is now the request part
        emit RequestedRandomness(requestId);
        //next part is a fullfilRandomness() where we are returned the random value
        //again, check on github. this part is a new function
        //till now its one transaction where we end the lottery and request a random number
    }

    //internal: as only to be called by our chainlink node and noone else (node calls VRFCoordinator which calls fulfullRandomness(), which we are overriding)
    //VRFConsumerBase has a definition already which we gotta override
    function fulfillRandomness(bytes32 _requestId, uint256 _randomness)
        internal
        override
    {
        require(
            lottery_state == LOTTERY_STATE.CALCULATING_WINNER,
            "You aren't there yet!"
        );
        require(_randomness > 0, "random-not-found");
        uint256 indexOfWinner = _randomness % players.length;
        recentWinner = players[indexOfWinner];
        recentWinner.transfer(address(this).balance);
        // Reset
        players = new address payable[](0);
        lottery_state = LOTTERY_STATE.CLOSED;
        randomness = _randomness;
    }
    /*
    function fulfillRandomnessxxxx(bytes32 _requestId, uint256 _randomness)
        internal
        override
    {
        require(
            lottery_state == LOTTERY_STATE.CALCULATING_WINNER,
            "Wrong state!"
        );
        require(_randomness > 0, "Random not found");
        //pick winner from list
        randomness = _randomness;
        uint256 winnerIndex = _randomness % players.length;
        recentWinner = players[winnerIndex];
        //pay this guy all the money
        recentWinner.transfer(address(this).balance);
        //reset the players

        players = new address payable[](0);
        lottery_state = LOTTERY_STATE.CLOSED;
    }*/
}
