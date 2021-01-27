# ImageRecognition-comicReader 🔭
This is a simple image recognition app (or Image processing app, in the strict sense) to process image passed to it as an input.

# ToolBox 🧰
* python@3.9.1
* (PIL) pillow@8.1.0

# Invocation in Terminal 🏃🏻‍♂️
`$ comic.py [options]`

Valid Options are: ✔️
```
 --version             show program's version number and exit
  -h, --help            show this help message and exit
  -q, --quiet           Don't print progress messages to stdout
                        [default:False]
  -d, --debug           Enable debug prints [default:True]
  -f FILE, --file=FILE  Name of the input file
  --prefix=PREFIX       Prefix for outputfiles
  --left-ignore=PIXELS  How much of the left margin to ignore when detecting
                        rows [default:0]
  --right-ignore=PIXELS
                        How much of the right margin to ignore when detecting
                        rows [default:0]
  --startrow=PIXELS     From which line of the each page (other than the first
                        page) should the processing start [default:0]
  --gutter-width=WIDTH  Minimum width of the gutter [default:15]
  --min-width=WIDTH     Minimum width of a frame [default:50]
  --min-height=HEIGHT   Minimum height of a frame [default:50]
```

# Alternative 🔃
- `git clone`
- `/nav/to/folder/containing/the/file`
- `python comic.py -h`  **or**  `python comic.py --help`

**Have a productive time writing code amigos & amigas !!** 🧸
