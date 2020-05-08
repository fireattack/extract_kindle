import re
from subprocess import run
import sys
from shutil import rmtree, which
import DumpAZW6_py3
import argparse
from pathlib import Path

LIB_PATH = Path(__file__).parent / 'lib'
DEDRM_PATH = LIB_PATH / R'DeDRM_App\DeDRM_lib\DeDRM_App.pyw'
CALIBRE_PATH = 'calibre-debug.exe' # Assuming in path already. R'C:\Program Files (x86)\Calibre2\calibre-debug.exe'


def main():

    if not which(CALIBRE_PATH):
        input('No calibre (calibre-debug.exe) found!')
        return 0

    parser = argparse.ArgumentParser()
    parser.add_argument("filepath")
    parser.add_argument(
        "-k", "--keep", action='store_true', help="keep temp and useless files")
    parser.add_argument(
        "-p",
        "--pause-at-end",
        action='store_true',
        help="pause on error or finish")
    args = parser.parse_args()

    p = Path(args.filepath)
    if not p.exists:
        print('Please provide a path to work on!')
        return 0

    print(f'Folder: {p}')

    azwFile = [f for f in p.iterdir() if (f.suffix.lower() in ['.azw', '.azw3'])]

    if len(azwFile) == 1:
        print(f'Processing {azwFile[0]}')
        run(['py', '-2', DEDRM_PATH, azwFile[0]])
        temp_folder = p / 'temp'
        azwFileDeDrmed = next(f for f in p.iterdir() if f.name.endswith('_nodrm.azw3'))
        run([CALIBRE_PATH, '-x', azwFileDeDrmed, temp_folder])

        if not args.keep:
            # Clean up `images` folder
            for f in (temp_folder / 'images').iterdir():
                if f.suffix.lower() in ['.unknown']:
                    print(f'Removing {f}..')
                    f.unlink()                
            imgs = [f for f in (temp_folder / 'images').iterdir() if f.suffix.lower() in ['.jpeg', '.jpg']]
            print(f'Removing {imgs[-1]}..')
            imgs[-1].unlink() # Remove the last image which is always a cover thumbnail.
            azwFileDeDrmed.unlink() # Remove deDRMed file.
    else:
        errMsg = 'No or more than one .azw file found!'
        if args.pause_at_end:
            input(errMsg)
        else:
            print(errMsg)
        return

    resFile = [f for f in p.iterdir() if (f.suffix.lower() in ['.res'])]

    if len(resFile) == 1:

        print(f'Processing {resFile[0]}')
        DumpAZW6_py3.main(['DumpAZW6_py3.py', str(resFile[0])])

        hdImages = [f for f in (p / 'azw6_images').iterdir() if f.suffix.lower() in ['.jpeg', '.jpg']]
        for img in hdImages:
            lowq_img = temp_folder / 'images' / img.name.replace('HDimage', '')
            if lowq_img.exists():
                print(f'Replacing {lowq_img.name} with {img.name}..')
                if not args.keep:
                    lowq_img.unlink()
                img.rename(lowq_img.with_suffix('.hd.jpeg'))
    else:
        print('No or more than one .res file found. Not processed.')

    # Find the title of the ebook from the HTML files.
    with (temp_folder / 'metadata.opf').open('r', encoding='utf8') as f:
        metadata = f.read()
    title = re.search(
        r'<dc:title>(.+?)</dc:title>', metadata, flags=re.DOTALL)[1].strip()

    for c in R'<>:"\/|?*':  # Windows-safe filename
        title = title.replace(c, '_')
    (temp_folder / 'images').rename(p / title)

    # Create an empty file to keep track of the the filename.
    # Eeaier to recognize which ebook is which after moving/removing the extracted files.
    (p / (title + '.txt')).open('a').close()
    
    if not args.keep:
        rmtree(temp_folder)
        if (p / 'azw6_images').exists():
            rmtree(p / 'azw6_images')
    if args.pause_at_end:
        input('All done!')


if __name__ == "__main__":
    main()
