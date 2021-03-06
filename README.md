# CS171_pa3

## High level design

Have each client take in a command line argument of its process number, and use that to get configuration from a config (yaml) file.

* One listening thread
  * Upon receiving message, pass connection into new thread to handle logic
  * puts message into shared event queue
* One consumer thread. Executes all logic.
  * When it needs to send out message, spawns new `sendMessage` thread
* Main thread to handle console input
  * upon restart, should run a check for saved state, and should rebuild off saved state file

## Paxos

Should use `TCP` in a try-catch for socket connections.

Each client should have the following variables:

* `BallotNum`: Past ballot process took part in (initially <0,0>)
* `AcceptNum`: Last ballot process accepted a value in, initially <0,0>
* `AcceptVal`: last accepted value (initially null)

Event Types:
* Proposal
* Promise
* Accept
* Accepted
* Decision

1. leader election (whoever has highest ballot number, ties broken by process id)

    * ("prepare", Ballot)

2. need quorum to elect leader

    * If ballot is bigger than process's, update ballot and reply with promise
    * Send last accepted ballot and value

3. leader checks acceptances

    * If all empty, send out your own
    * Otherwise, send value with highest ballot

4. Upon receiving accept
    * Each process updates acceptNum and acceptVal
    * Accept if ballot is greater than their last one
 

## Blockchain

## Failures

* Upon crash, save state of the process

### Fail Connection

* Store connections in a dictionary
* Check if connection is open before sending a message
* Block a reception by dropping messages

## text cases

- Multiple processes competing for Paxos
- Recovery after crashing mid paxos
- no possible quorum
- crash after block computed before getting accepted
- fail link with majority
- stale message recovery off a proposal
- stale message recovery off an accept
- Stale message recovery off incorrect process
