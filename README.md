Midware
=======

A simple general-purpose middleware library for Python 3.5 or greater.

Often the main task of a program can
be represented as one function with rather
straightforward input and output. But a lot of
unrelated code needs to be added to make this one function
doing one main task into an actual usable utility that,
for example, handles user input correctly.

One way to decomplect unrelated concerns in a program is a middleware pattern.

Middleware puts functions and composability first. To make it
easier for functions with different signatures to be composable all
arguments are usually packed into one dictionary called `ctx` for "context".
All functions take `ctx` as an argument, modify it and return it.

Functions that modify the `ctx` are called handlers. Handlers are already
very composable by design and one can easily pipe `ctx` values through
a series of handlers, but that's often not enough. One of the most frequently
used patterns (a lot of languages even have built-in keywords for it, Python has several actually)
is the "setup-teardown" pattern. That is where middleware comes in.

Middleware is a higher-order function that takes a handle and return a new handle,
which typically wraps the old one. It does some work, maybe modifies the `ctx`,
passes it to the old handle, gets a new `ctx` back and optionally does
something else before returning.

Once again, middleware is composable, because it takes handles and returns handles.
When using middleware as building blocks, composing those returns an outermost handle,
which needs to be called with a `ctx` value as an argument to kick off the computation.
