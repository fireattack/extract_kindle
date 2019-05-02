import re
import subprocess
import sys
import locale
from os import chdir, listdir, makedirs, remove, rename, walk, system
from os.path import basename, dirname, exists, isdir, isfile, join, splitext
from shutil import rmtree
import DumpAZW6_py3
import argparse

LIB_PATH = join(dirname(sys.argv[0]), 'lib')
DEDRM_PATH = join(LIB_PATH, R'DeDRM_App\DeDRM_lib\DeDRM_App.pyw')
EBOOKCONVERT_PATH = R'C:\Program Files (x86)\Calibre2\calibre-debug.exe'


def changeCodePageBack():
    cp = locale.getpreferredencoding().replace('cp', '')
    system('chcp '+cp)


def run(cmdStr):

    print(cmdStr)
    subprocess.call(cmdStr)


def main():
    changeCodePageBack()

    if not exists(EBOOKCONVERT_PATH):
        input('No calibre (ebook-convert.exe) found!')
        return 0

    parser = argparse.ArgumentParser()
    parser.add_argument("filepath")
    parser.add_argument("-k", "--keep", action='store_true',
                        help="keep temp files")
    parser.add_argument("-p", "--pause-at-end",
                        action='store_true', help="pause on error or finish")
    args = parser.parse_args()

    if exists(args.filepath):
        myPath = args.filepath
    else:
        print('Please provide a path to work on!')
        return 0

    print(f'Folder: {myPath}')
    chdir(myPath)  # Change working dir

    azwFile = [
        f for f in listdir('.')
        if (splitext(f)[1].lower() in ['.azw', '.azw3'])
    ]

    if len(azwFile) == 1:
        print(f'Processing {azwFile[0]}')
        run(f'py -2 "{DEDRM_PATH}" "{azwFile[0]}"')

        azwFileDeDrmed = next(
            f for f in listdir('.') if f.endswith('_nodrm.azw3'))
        subprocess.run([EBOOKCONVERT_PATH, '-x', azwFileDeDrmed, 'temp'])
        # Ebook-convert.exe used to have a bug that always changes chcp to 65001, which breaks `print()` in Python badly. 
        # So we change it back manually. I keep it even after the bug is fixed just to be safe.
        changeCodePageBack()
        if not args.keep:
            remove(azwFileDeDrmed)
    else:
        errMsg = 'No or more than one .azw file found!'
        if args.pause_at_end:
            input(errMsg)
        else:
            print(errMsg)
        return

    resFile = [
        f for f in listdir('.')
        if (splitext(f)[1].lower() in ['.res'])
    ]

    if len(resFile) == 1:

        print(f'Processing {resFile[0]}')

        DumpAZW6_py3.main(['DumpAZW6_py3.py', resFile[0]])

        hdImages = [
            f for f in listdir('azw6_images')
            if (splitext(f)[1].lower() in ['.jpeg', '.jpg'])
        ]

        for img in hdImages:
            lowqImage = join('temp\\images',
                             img.replace('HDimage', ''))
            if exists(lowqImage):
                print(f'Replacing {lowqImage} with {img}..')
                if not args.keep:
                    remove(lowqImage)
                rename(join('azw6_images', img),
                       lowqImage.replace('.jpeg', '.hd.jpeg'))
    else:
        print('No or more than one .res file found.')

    # Find the title of the ebook from the HTML files.
    with open('dir\\metadata.opf', 'r', encoding='utf8') as f:
        metadata = f.read()
    title = re.search(
        r'<dc:title>(.+?)</dc:title>', metadata,
        flags=re.DOTALL)[1].strip()

    for c in R'<>:"\/|?*':  # Windows-safe filename
        title = title.replace(c, '_')
    rename('temp\\images', title)

    # Create an empty file to keep the filename.
    # Eeaier to recognize which ebook is which after moving/removing the extracted files.
    open(title + '.txt', 'a').close()
    if not args.keep:
        rmtree('temp')
    if exists('azw6_images') and not args.keep:
        rmtree('azw6_images')
    if args.pause_at_end:
        input('All done!')


if __name__ == "__main__":
    main()
