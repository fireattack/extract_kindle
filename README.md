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

4. Run Kindle application, download a few books (important), and create dump file by Task Manager -> Details -> Right click on `kindle.exe` -> Create dump file. Mark the file path.

5. Run the script `python extract_kindle.py init <dump_file>` to initialize the configuration (if does not exist) and create a minidump file for future use. The default config file will be created at `./config.json`. Afterwards, the script will try to read the config file from (in order of priority):
    - `config.json` in the current directory.
    - `config.json` in the directory where `extract_kindle.py` is located.
    - `.extract_kindle_config.json` in the home directory.

    Once finished, you can delete the original dump file to save space. The saved minidump file (it's a text file, open it in editor) should have at least one non-zero "Working secret". If not, you probably want to download more books and try it again.

6. Check the generated `config.json` file and make necessary adjustments (e.g. move keys.txt and minidump files to a more suitable location). The `config.json` file contains the following keys:
    - `dump_file`: Path to the dump file.
    - `keys_file`: Path to the keys file.
    - `kindle_content_dir`: Path to `My Kindle Content` directory.
    - `kindle_dir`: Path to the Kindle application directory (optional; if not set, it uses `%localappdata%\Amazon\Kindle\application\`).

7. Run the script again with `python extract_kindle.py <book_dir>` to extract a book, or `python extract_kindle.py` to extract all books.


```
usage: extract_kindle.py [-h] [-O DIRECTORY] [COMMAND] [ARGUMENTS ...]

Extracts and decrypts Kindle books.

positional arguments:
  COMMAND               Optional command to execute:
                            (no command)       - Decrypt all books in 'My Kindle Content' folder.
                            init <dumpfile>    - Initialize and save keys from a Kindle dump file. The <dumpfile> path is required.
                            <book_folder_path> - Decrypt a specific book from its folder path.
  ARGUMENTS             Additional arguments for the command (e.g., <dumpfile> for "init")

options:
  -h, --help            show this help message and exit
  -O DIRECTORY, --outdir DIRECTORY
                        Output directory for decrypted books (default: current directory)
```
