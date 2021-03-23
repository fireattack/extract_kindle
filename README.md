# extract_kindle

## Highlights

* Basically a CLI wrapper to use DeDRM_tools by apprenticeharper without using Calibre GUI
* Support extract HDImage from .res file
* Key will be placed at `./kindlekey1.k4i` after extracted for the first time.

## Installation

1. Clone the repo.
1. Install calibre and edit `config.json`'s calibre key to your `calibre-debug.exe` path
1. (Optional) install WinRAR and edit `config.json`'s rar key to your `Rar.exe` path
1. Clone https://github.com/apprenticeharper/DeDRM_tools repo and place "DeDRM_plugin" folder and its content directly into this repo's root folder.

## Usage 

```
usage: extract_kindle.py [-h] [-k] [-z] [-o OUTPUT] dir

positional arguments:
  dir                   choose the folder contains DRMed azw file(s)

optional arguments:
  -h, --help            show this help message and exit
  -k, --keep            keep temp and useless files
  -z, --compress        also compress the files
  -o OUTPUT, --output OUTPUT
                        output folder (default: same as dir)
```

Examples:

```
extract_kindle.py "G:\_temp\My Kindle Content\B00KYFFDV2_EBOK" -o "D:\output" -z
extract_kindle.py "G:\_temp\My Kindle Content\B00KYFFDV2_EBOK"
```

You can also use it as a module by something like 
```py
extract_kindle.main(R"G:\_temp\My Kindle Content\B00KYFFDV2_EBOK", "-o", "D:\\output", "-z")
```