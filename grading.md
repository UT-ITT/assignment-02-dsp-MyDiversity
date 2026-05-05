# MyDiversity (11.5/15P)

## 1 - Karaoke Game (7/7P)
* frequency detection works correctly and robustly
    * yep, silence results in FFT-chaos, but the rest works! (3P)
* the game is playable, does not crash, and is (kind of) fun to play
    * yep (2P)
* the game tracks some kind of score for correctly sung notes
    * yep (1P)
* low latency between input and detection
    * yep (1P)


## 2 - Whistle Input (4/7P)
* upwards and downwards whistling is detected correctly and robustly
    * script doesn't run robustly, detection would work, but a threshold over time is missing propably (1.5P)
*  detection is robust against background noise
    * speaking triggeres everything (0.5P)
* low latency between input and detection
    * yep (1P)
* triggered key events work
    * yep (1P)


## Code-Quality and .venv used (0.5/1P)
* input device is hardcoded 