# extract_kindle

## Highlights

* Basically a CLI wrapper to use DeDRM_tools by apprenticeharper without using Calibre GUI
* Support extract HDImage from .res file
* Key will be placed at `./kindlekey1.k4i` after extracted for the first time.

## Installation

1. Download newest release and uncompress.
1. Install calibre, and edit `config.json`'s calibre key to your `calibre-debug.exe` path.
1. (Optional) create some post-prosssing command and put into `config.json`'s `postprocessing` key. Remember to add quotes and escape special characters if needed! You can check the example `config-example.json` to get an idea.
1. Install Python3, and then pycryptodome (`pip install pycryptodome`)

### From source

1. Clone the repo.
1. Install calibre and edit `config.json`'s calibre key to your `calibre-debug.exe` path.
1. (Optional) create some post-prosssing command and put into `config.json`'s `postprocessing` key. Remember to add quotes and escape special characters if needed! You can check the sample config.json to get an idea.
1. Clone https://github.com/apprenticeharper/DeDRM_tools repo and place "DeDRM_plugin" folder and its content directly into this repo's root folder.
1. Install pycryptodome (`pip install pycryptodome`)

## Usage

```
usage: extract_kindle.py [-h] [-k] [-p] [-o OUTPUT] dir

positional arguments:
  dir                   choose the folder contains DRMed azw file(s)

optional arguments:
  -h, --help            show this help message and exit
  -k, --keep            keep temp and useless files
  -p, --postprocessing  do some postprocessing with the file.
  -o OUTPUT, --output OUTPUT
                        output folder (default: same as dir)
```

Examples:

```
extract_kindle.py "G:\_temp\My Kindle Content\B00KYFFDV2_EBOK" -o "D:\output" -p
extract_kindle.py "G:\_temp\My Kindle Content\B00KYFFDV2_EBOK"
```

You can also use it as a module by something like
```py
extract_kindle.main(R"G:\_temp\My Kindle Content\B00KYFFDV2_EBOK", "-o", "D:\\output", "-p")
```

## Post-processing template string substitution

Remember to add quotes around them if needed!

* $o: output root path (i.e. -o parameter)
* $f: book name string (path-safe, extracted from Kindle info)
* $p: full path of the folder contains the image files (basically, $o/$f)