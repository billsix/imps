=======================================
IWADs, PWADs, and the lump filesystem
=======================================

An engine is nothing without its data. *Doom* keeps that data in WAD files, and
before the main loop from Chapter 1 can run, the engine has to answer two
questions: **which base game is this**, and **how do I turn a name like**
``E1M1`` **into the bytes of that map?** This chapter reads the code that answers
both. The vocabulary — WAD, lump, IWAD, PWAD — is in the introduction; keep it
handy.

Many files, one virtual filesystem
===================================

Start with the second question, because everything else stands on it. Doom
addresses all of its content by *name*: give the engine a lump name and it hands
back bytes, without the game code ever caring which file on disk they came from.
That illusion is built by loading every WAD — the IWAD first, then each PWAD — into
one merged namespace:

.. literalinclude:: ../../checkout/gzdoom/src/common/filesystem/source/filesystem.cpp
   :language: cpp
   :start-after: // doc-region-begin init_multiple_files
   :end-before: // doc-region-end init_multiple_files
   :caption: FileSystem::InitMultipleFiles — src/common/filesystem/source/filesystem.cpp

Two things earn their place here. First, ``InitSingleFile`` — the tiny wrapper at
the top — is just ``InitMultipleFiles`` with a one-element list; we will use it in
a moment to peek inside a single WAD without disturbing the real game filesystem.

Second, read the comment on ``InitMultipleFiles`` itself: *"The name searcher
looks backwards, so a later file can override an earlier one."* That one sentence
is the whole mod system. The engine ``AddFile``\ s each WAD in order and, when you
ask for a lump, searches from the **last** file loaded toward the first. Because
the IWAD is loaded first and PWADs after it, a PWAD that contains its own ``E1M1``
simply *wins* — the base game's map is still in memory, but the searcher finds the
add-on's copy first. There is no patching, no merging of file contents: override
is a pure consequence of load order plus a backward search. At the end, one hash
table (``InitHashChains``) makes every name-to-lump lookup fast.

Recognizing a WAD by what is inside it
======================================

Now the first question: which game is this? GZDoom does **not** trust the
filename — ``doom2.wad`` might be renamed, and total-conversion mods ship their
own IWADs. Instead it opens the WAD and looks at the lumps inside:

.. literalinclude:: ../../checkout/gzdoom/src/d_iwad.cpp
   :language: cpp
   :start-after: // doc-region-begin scan_iwad
   :end-before: // doc-region-end scan_iwad
   :caption: FIWadManager::ScanIWAD — src/d_iwad.cpp

This is the ``InitSingleFile`` from the previous section put to work:
``check.InitSingleFile(iwad, …)`` loads just this one candidate as a throwaway
filesystem, so ``ScanIWAD`` can walk its entries without touching the game's real
data. Each known game has a *signature* — a small set of lump names it must
contain — and the engine keeps a bitmask, ``mLumpsFound``, one bit per required
lump. The loop visits every lump in the file; ``CheckFileName`` sets the matching
bit for every game whose signature mentions that name (maps get special handling,
since a ``maps/E1M1`` entry should count as ``E1M1``). At the end, a game matches
only when **all** of its signature bits are set — ``mLumpsFound[i]`` equals the
full mask ``(1 << count) - 1`` — and the index of that game is returned. Identity
by contents, not by name: the same trick a file-type detector uses on magic
bytes, scaled up to "which entire game is this."

When the engine has to ask
==========================

Scanning can be ambiguous. You might have several IWADs installed, or none that
the engine can pin down from the command line. When that happens, GZDoom puts up
its startup **IWAD picker** — the dialog box that asks *"which game do you want to
play?"* Here is the code that decides whether to show it:

.. literalinclude:: ../../checkout/gzdoom/src/d_iwad.cpp
   :language: cpp
   :start-after: // doc-region-begin iwad_picker_decision
   :end-before: // doc-region-end iwad_picker_decision
   :caption: the IWAD-picker decision — src/d_iwad.cpp (FIWadManager::IdentifyVersion)

The gate is one line:

.. code-block:: cpp

   bool alwaysshow = (queryiwad && !Args->CheckParm("-iwad") && !foundprio);

The picker appears when the ``queryiwad`` setting is on **and** the user did not
name a WAD with ``-iwad`` on the command line **and** no prioritized IWAD was
found — or, regardless, whenever more than one candidate was discovered
(``picks.Size() > 1``). If it shows, ``I_PickIWad`` blocks on the GUI until the
player chooses; the chosen game becomes the new default, and the extra autoload
flags come back through the dialog. Only after this does the code fall through to
the load sequence — the comment *"zdoom.pk3 must always be the first file loaded
and the IWAD second"* is the very load order the previous section described.

.. admonition:: Why this excerpt is here
   :class: note

   This decision is exactly where the *imps* GZDoom carrier does its work. The
   maintainer wants to launch a WAD straight from the command line and **skip**
   this picker; the planned patch changes the ``alwaysshow`` logic so a
   CLI-supplied WAD just plays. Reading the condition above is how you would know
   what to change and why. The book stays comment-only against upstream; the
   behavior change lives in the carrier's separate patch stream.

Put the two chapters together and the engine's opening move is complete: it has
identified the game (``ScanIWAD``), possibly asked you to confirm it (the picker),
and merged the IWAD and any PWADs into one searchable filesystem
(``InitMultipleFiles``). The main loop from Chapter 1 can now ask for ``E1M1`` by
name and get a map back — and the game begins.
