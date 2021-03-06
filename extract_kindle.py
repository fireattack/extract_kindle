import re
from subprocess import run
import sys
from shutil import rmtree, which, move
import DumpAZW6_py3
import argparse
from pathlib import Path
import json


DEDRM_PATH = Path(__file__).parent / 'DeDRM_plugin'
KEY = Path(__file__).parent / "kindlekey1.k4i"

sys.path.insert(0, str(DEDRM_PATH)) # Does not support Path-like obj
from k4mobidedrm import decryptBook
from kindlekey import getkey

# Just for reference, if you want to use them as CLI:
# run(['py', DEDRM_PATH / 'kindlekey.py', Path(__file__).parent]) -- get key
# run(['py', DEDRM_PATH / 'k4mobidedrm.py', "-k", KEY, azw_files[0], p]) -- deDRM

def main(*input_args):
    parser = argparse.ArgumentParser()
    parser.add_argument("dir", help="choose the folder contains DRMed azw file(s)")
    parser.add_argument("-k", "--keep", action='store_true', help="keep temp and useless files")
    parser.add_argument("-z", "--compress", action='store_true', help="also compress the files")
    parser.add_argument("-o", "--output", help="output folder (default: same as dir)")
    args = parser.parse_args(input_args)

    # load config
    config = dict(calibre='calibre-debug.exe', rar=R'C:\Program Files (x86)\WinRAR\Rar.exe') # default
    try:
        config_file = Path(__file__).parent / 'config.json'
        if config_file.exists():
            with config_file.open('r', encoding='utf-8') as f:
                config = json.load(f)
            print('Loaded config from config.json')
    except:
        pass

    if not which(config['calibre']):
        print('No calibre (calibre-debug.exe) found!')
        return 1

    has_rar = True
    if not which(config['rar']):
        print('No WinRAR (Rar.exe) found. --compress function disabled.')
        has_rar = False

    p = Path(args.dir)
    if not p.exists():
        print('Please provide a path to work on!')
        return 1

    print(f'Folder: {p}')

    azw_files = [f for f in p.iterdir() if (f.suffix.lower() in ['.azw', '.azw3'])]
    azw_files_DeDrmed = [f for f in p.iterdir() if f.name.lower().endswith('_nodrm.azw3')]
    deDRM = False
    if len(azw_files) == 0:
        print('No .azw file found!')
        return 1
    elif len(azw_files_DeDrmed) == 1:
        deDRMed_azw_file = azw_files_DeDrmed[0]
    elif len(azw_files) == 1:
        print(f'DeDRMing {azw_files[0].name}..')
        if not KEY.exists():
            getkey(str(Path(__file__).parent))
        if not KEY.exists():
            print('Failed to get key!')
            return 1

        decryptBook(azw_files[0], str(p), [str(KEY)], [], [], [])

        deDRMed_azw_file = next(f for f in p.iterdir() if f.name.endswith('_nodrm.azw3'))
        deDRM = True # this flags that the deDRMed file is created by ourselves (wasn't there before). So we remove it later.

    print(f'Extracting from {deDRMed_azw_file.name}..')
    temp_folder = p / 'temp'
    run([config['calibre'], '-x', deDRMed_azw_file, temp_folder])
    if not args.keep:
        # Clean up `images` folder
        for f in (temp_folder / 'images').iterdir():
            if f.suffix.lower() in ['.unknown']:
                print(f'Removing {f}..')
                f.unlink()
        imgs = [f for f in (temp_folder / 'images').iterdir() if f.suffix.lower() in ['.jpeg', '.jpg']]
        # The last image which is always a cover thumbnail. Here just some quick check to make sure. Then remove.
        assert imgs[-1].stat().st_size <= 50*1024
        assert int(imgs[-1].stem)  == int(imgs[-2].stem) + 2
        print(f'Removing {imgs[-1]}..')
        imgs[-1].unlink()
        if deDRM:
            deDRMed_azw_file.unlink() # Remove deDRMed file.

    res_files = [f for f in p.iterdir() if (f.suffix.lower() in ['.res'])]
    if len(res_files) == 1:

        print(f'Processing resource file {res_files[0]}..')
        DumpAZW6_py3.main(['DumpAZW6_py3.py', str(res_files[0])])

        hd_images = [f for f in (p / 'azw6_images').iterdir() if f.suffix.lower() in ['.jpeg', '.jpg']]
        for img in hd_images:
            lowq_img = temp_folder / 'images' / img.name.replace('HDimage', '')
            if lowq_img.exists():
                print(f'Replacing {lowq_img.name} with {img.name}..')
                if not args.keep:
                    lowq_img.unlink()
                img.rename(lowq_img.with_suffix('.hd.jpeg'))
    else:
        print('No or more than one .res file found. Not processed.')

    # Find the title of the ebook from the metadata file.
    metadata = (temp_folder / 'metadata.opf').read_text(encoding='utf8')
    title = re.search(r'<dc:title>(.+?)</dc:title>', metadata, flags=re.DOTALL)[1].strip()

    for c in '<>:"\/|?*\r\n\t':  # Windows-safe filename
        title = title.replace(c, '_')

    if args.output:
        save_dir = Path(args.output)
        save_dir.mkdir(parents=True, exist_ok=True)
    else:
        save_dir = p

    print(f'Moving files to {save_dir}..')
    new_folder = save_dir / title
    move((temp_folder / 'images'), new_folder)

    # Create an empty file to keep track of the the filename.
    # Easier to recognize which ebook is which after moving/removing the extracted files.
    (p / (title + '.txt')).open('a').close()

    if args.compress and has_rar:
        zip_name = new_folder.with_name(new_folder.name + '.rar')
        run([config['rar'], 'a', '-r', '-ep1', '-rr5p', '-m0', zip_name, str(new_folder) + "\\*"])

    if not args.keep:
        rmtree(temp_folder)
        if (p / 'azw6_images').exists():
            rmtree(p / 'azw6_images')

    print('All done!')


if __name__ == "__main__":
    args = sys.argv[1:]
    main(*args)
