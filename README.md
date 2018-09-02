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

Finally, you'll want a `cmd.py` which launches either the server or the client.

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

### Complex multi-stage remote communication

Typically, calls from the `Player` to the `Game` are handled as synchronously
as possible - which is to say, the `Player` waits until it has a response from
the `Game` before contining.

However, in some cases methods on the `Game` are long-running. In those cases,
we don't want the `Player` to wait around for a response. Instead, it posts
a request for the `Game` to take some action, then polls regularly to see if
a value has been returned yet.

In particular, methods on the `Game` class that

- are called by the `Player` class, and
- call back out to a `Player` class

should be marked as long-running. This is done by adding a pseudo-variable,
`_await=False`, to the `Game` method signature.

Methods on the `Player` class that

- call methods on the `Game` marked with `_await=False`

must also be annotated with a `_await=False` argument.

## Helper classes

There's a `remoter.BasePlayer` class which contains three remotable methods:
`print`, `input` and `exit`. The examples use these pretty heavily; however,
it's recommended to put more complex interactions that can live predominantly
on the player side in their own methods. (See the 'battleships' example for
this.)

## To install:

    pip install -e .

## Running the battleships game

### As a single process

    python battleships/game.py

### As a server/client

- Launch the server:

      % batsrv
      ======== Running on http://0.0.0.0:8080 ========
      (Press CTRL+C to quit)
    
  (or `python battleships/cmd.py`)

- Launch the first client:

      % batcli
      --game 4514826560
      --as 1741
      Player 1 pick your ships!

- Connect to the same game with a second client:

      % batcli --game 4514826560
      --as 1340
      Player 2 pick your ships!

  The `--as 1340` command-lilne option will permit reconnecting as the same player if this client dies.

- Additional client connections are rejected:

      % batcli --game 4514826560
      --as 7072
      Too many players already connected to this game.
