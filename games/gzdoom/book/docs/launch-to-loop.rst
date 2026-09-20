================================
From launch to the main loop
================================

Every game engine, underneath the graphics, is one loop: read input, advance the
world a little, draw, repeat, forever, until the player quits. This chapter
follows GZDoom from the process's single entry point down into that loop. All
three excerpts are from ``src/d_main.cpp``, the file whose comment header calls
itself *"DOOM main program (D_DoomMain) and game loop (D_DoomLoop)."*

One door in, one door out
=========================

However tangled a large program gets, it is far easier to reason about when it
has exactly *one* place it starts and *one* place it ends. GZDoom does. Platform
startup code (the OS ``main``) hands off almost immediately to ``GameMain``,
which is that single door:

.. literalinclude:: ../../checkout/gzdoom/src/d_main.cpp
   :language: cpp
   :start-after: // doc-region-begin game_main_entry
   :end-before: // doc-region-end game_main_entry
   :caption: GameMain — src/d_main.cpp

Read the shape rather than every line. ``GameMain`` sets up the console and its
CVars (Doom's configuration variables), then runs the whole game inside a
``try`` — ``D_DoomMain_Internal()`` is where everything happens. The two
``catch`` clauses are the *only* sanctioned way out: a ``CExitEvent`` thrown from
somewhere deep in the code (the comment is blunt — *"No more 'exit', please."*),
or a C++ exception that becomes a fatal-error dialog. Whichever fires, control
lands at the same place, and the long tail of shutdown calls runs in a fixed
order — stop sound, collect garbage, close the window, save the config, free the
arguments. Startup ran forward; shutdown runs in reverse. That symmetry is not
decoration: it is how the engine guarantees it never leaks the window, the audio
device, or the player's settings, no matter how it exits.

The handoff into the loop
=========================

``D_DoomMain_Internal`` is long — it parses the command line, mounts the data,
builds the game state. We will not read all of it here; we join it at the very
end, at the moment it stops *preparing* and starts *playing*:

.. literalinclude:: ../../checkout/gzdoom/src/d_main.cpp
   :language: cpp
   :start-after: // doc-region-begin startup_to_loop
   :end-before: // doc-region-end startup_to_loop
   :caption: entering the game — src/d_main.cpp (end of D_DoomMain_Internal)

``D_InitGame`` finishes wiring up the identified game, and then the last real
statement is a bare call: ``D_DoomLoop()``. The comment beside it is the whole
point of the chapter — *"this only returns if a 'restart' CCMD is given."*
Ordinarily the loop never comes back; the program lives inside it for the rest of
the session. The surrounding ``do { … } while (1)`` exists solely so that a
console *restart* command can fall out of the loop, clean up, and re-enter with
fresh state — the engine rebuilds itself in place rather than relaunching the
process.

The loop itself
===============

Here is the loop the program spends its life in:

.. literalinclude:: ../../checkout/gzdoom/src/d_main.cpp
   :language: cpp
   :start-after: // doc-region-begin doom_loop
   :end-before: // doc-region-end doom_loop
   :caption: D_DoomLoop — src/d_main.cpp

Strip away the details and it is the classic engine heartbeat. Every iteration:

1. **Timekeeping.** ``I_StartFrame`` / ``I_SetFrameTime`` establish how much real
   time has passed, so the simulation can run at a fixed rate independent of how
   fast the machine draws.
2. **Advance the simulation.** This is the fork in the loop. The normal path is
   ``TryRunTics()`` — Doom's world updates in fixed steps called *tics* (35 per
   second), and ``TryRunTics`` runs as many whole tics as the elapsed time and
   the network owe, no more. The ``singletics`` branch above it is the debug
   path: run exactly one tic per frame, spelling out by hand the same sequence
   ``TryRunTics`` performs — poll input, build a command, tick the console, the
   menu, the game, the sounds. Keeping the simulation on a fixed clock while the
   *drawing* runs as fast as it can is the single most important structural
   decision in the engine; the whole ``d_main`` loop exists to enforce it.
3. **Draw.** ``D_Display()`` renders the current world state to the screen, and
   ``S_UpdateMusic`` keeps the soundtrack fed.
4. **Check for a restart.** ``wantToRestart`` is the one flag that lets the loop
   ``return`` — back to the ``do/while`` we just saw.

Then the whole thing is wrapped in ``try``/``catch``. A recoverable error
mid-frame — a broken script, a bad file — does not crash the game: it prints the
message and calls ``D_ErrorCleanup()``, and the loop simply continues to the next
iteration. An engine that runs untrusted, community-made content has to survive
that content misbehaving, and this is where it does.

.. graphviz::

   digraph launch {
     rankdir=TB;
     node [shape=box, fontname="sans-serif"];
     os     [label="OS main"];
     gm     [label="GameMain\n(the one door in/out)"];
     dmi    [label="D_DoomMain_Internal\n(parse args, mount data,\nbuild game state)"];
     loop   [label="D_DoomLoop\n(for(;;): time -> tics -> draw)", style=filled, fillcolor="#e8e8e8"];
     os -> gm -> dmi -> loop;
     loop -> loop [label="every frame"];
     loop -> dmi [label="restart CCMD", style=dashed, constraint=false];
   }

Everything the rest of this book describes — finding the data (next chapter),
rendering, scripting — is either something ``D_DoomMain_Internal`` sets up before
the loop, or something that happens on one pass *through* the loop. Fix these two
shapes in your head, the single-entry startup and the fixed-tic loop, and the
rest of the engine has a frame to hang on.
