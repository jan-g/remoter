# Remoter framework for dojo projects

Having seen another Dojo project that knocked up a client/server for
its solution, I wondered if there was a way to make a lightweight
remoting framework that'd let us run a single in-process "game",
talking directly to the client objects (with no intermediaries) -
or alternatively, permit wiring up of a server and client.

The goal is to require minimal or no code changes to the remoted source.

## How it works - a strategy for using this

Firstly, put all of your actual state and behaviour into a standard class.
(This also makes life easier when working in a small team in a dojo -
someone can handle the main lifecycle, someone can work on the class
implementation, etc.)

Then, write your driver in two parts: a main Game (this'll become the
server-hosted class) and a Player (which runs on the client).

## What happens in the server / client setup

The `Game` class receives notifications when new players connect: this is
done by launching a coroutine, `new_player`, with each new player.

The `Game` can/should call out to the `Player` to sort out any preliminary
setup: this might include letting each `Player` know their 'player number'
or other identifier.

Once the requisite number of players are assembled, the `Game` can spawn
one (or more) coroutines to handle the main logic. This can call out to
`Players` as required.

## Remote communication

The basic rule of thumb here is that all communication between the `Game`
and the `Player` (or vice-versa) should be done asynchronously. This has
two mechanical consequences:

- every method that is going to be called across the `Game`/`Player` divide
  must be declared with `async def` to mark it as a coroutine;

- each remote call must be `await`ed.

In addition, there is a third requirement that's a practical consequence
of the way the client/server framework is implemented:

- each call from the `Player` to the `Game` should return rapidly. Therefore,
  if the call can trigger a long-running activity on the `Game` side, that
  activity should live inside its own coroutine that the `Game` class spawns.

  `asyncio.create_task` can be used for this purpose.

## Helper classes

There's a `remoter.BasePlayer` class which contains three remotable methods:
`print`, `input` and `exit`. The examples use these pretty heavily; however,
it's recommended to put more complex interactions that can live predominantly
on the player side in their own methods. (See the 'battleships' example for
this.)

## To install:

    pip install -e .
