# extract_kindle - NEW

This is a new version of extract_kindle (Kindle ebook extraction automation tool) that can work with newest Kindle.

The code is basically copied from a forked version of [DeDRM_tools](https://github.com/Satsuoni/DeDRM_tools) by Satsuoni, as well as [KFX Input plugin](https://www.mobileread.com/forums/showthread.php?t=291290).

The original python code has be dramatically simplified by removing all kinds of messy code. E.g.:

* Removed all the Python 2 compatibility code.
* Change all the imports to relative imports.
* Support pycryptodome (Crypto) only.
* Support only the native lzma module.
* Remove all kinds of stdout/stderr hacks.
* TODO: remove all the CLI related code.
* TODO: remove all the GUI related code.


## Usage

1. Clone the repository.
2. Install the required dependencies using `pip install -r requirements.txt`.
3. Download `KRFKeyExtractor.exe` from [Satsuoni's DeDRM_tools repository](https://github.com/Satsuoni/DeDRM_tools/releases/tag/v10.0.10) and place it in the same directory as `kindle.exe` (by default, it's in `%localappdata%\Amazon\Kindle\application\`).
4. Run Kindle application, and create dump file by Task Manager -> Details -> Right click on `kindle.exe` -> Create dump file.
5. Run the script `python extract_kindle.py init <dump_file>` to initialize the configuration and create a minidump file for future use. Afterwards, you can delete the original dump file to save space.
6. Check the generated `config.json` file and make necessary adjustments (e.g. move keys.txt and minidump files to a more suitable location). The `config.json` file contains the following keys:
    - `dump_file`: Path to the dump file.
    - `keys_file`: Path to the keys file.
    - `kindle_content_dir`: Path to `My Kindle Content` directory.
    - `kindle_dir`: Path to the Kindle application directory (optional; if not set, it uses `%localappdata%\Amazon\Kindle\application\`).

7. Run the script again with `python extract_kindle.py <book_dir>` to extract a book, or `python extract_kindle.py` to extract all books.


```
usage: extract_kindle.py [-h] [-O OUTDIR] [command] [args ...]

positional arguments:
  command
  args

options:
  -h, --help            show this help message and exit
  -O OUTDIR, --outdir OUTDIR
                        Output directory for decrypted books
```
