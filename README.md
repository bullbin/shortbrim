# shortbrim
Depreciated Python-based engine reimplementation for early NDS Layton games.

# What this is, and what this isn't
**shortbrim** is an experimental high-level reimplementation of parts of the Layton game engine.
It was written for fun and is not based on decompilation, just observation.

## Features include...
* Game backup support, no unpacking required
* Interactive puzzle playback
* Hit-or-miss event playback
* Incomplete room playback

## Features don't include...
* Great code design
* Amazing compatibility
* Complete support for puzzles
* Complete support for events
* Complete support for rooms
* Support for story, nor progression
* Support for sound or movies
* Guarenteed multi-lingual support - only English tested
* Bulletproof research

**shortbrim** alone cannot play anything fully, or to an enjoyable degree.
Many features are missing and left incomplete.
It is best used as a debugging tool, and useful for any researchers looking into the game.

Expect bugs, and identical behaviour to the games themselves is not guarenteed.
Have fun exploring various files inside the game, looking at individual room states, playing individual events, etc.
Feel free to use any research about assets, loading routines, events, pathing and binary formats.

**shortbrim** has since been adapted into a library, **madhatter**.
The engine was rewritten as **widebrim**, which is accurate and based on reverse-engineering, but is LAYTON2 specific.
**widebrim** has full story support so the game can be played properly.
It will be open sourced when it is ready. In the meantime, please enjoy **shortbrim**!

If you use any parts of this code, please credit me or the original contributor! Alternatively if you need clarification, send an issue or contact me.

## Compatibility
* LAYTON1 (Professor Layton and the Curious Village)
* LAYTON2 (Professor Layton and the Diabolical / Pandora's Box)

LAYTON2 is recommended over LAYTON1. It is far more developed.

## Requirements
* Python 3
* pygame - developed with 1.9.x, probably works on later versions
* ndspy
* Pillow

## Setup
* Install all dependencies above
* Clone correct branch - **master** branch for LAYTON1, **layton2** branch for LAYTON2
* Add game backup to root folder (recommended) - call it rom2.nds for LAYTON2, or rom1.nds for LAYTON1
* Alternatively, use the unpacking script in the tools folder to convert assets to more friendly formats.
This is legacy though, and has worse compatibility and may introduce bugs. Use with caution.
The paths for both unpacked and packed assets can be changed in conf.py
* Finally, open the handler of your choice from the engine folder. Edit the last lines to change parameters.

## Credits
* Tinke for reversing and research
* DSDecmp for file routines

Any missed credits should be given inside files, please raise an issue if I've missed someone!
