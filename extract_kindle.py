import re
from subprocess import run
import sys
from shutil import rmtree, which, move
import DumpAZW6_py3
import argparse
from pathlib import Path

LIB_PATH = Path(__file__).parent / 'lib'
DEDRM_PATH = LIB_PATH / R'DeDRM_App\DeDRM_lib\DeDRM_App.pyw'
CALIBRE_PATH = 'calibre-debug.exe' # Assuming in path already. R'C:\Program Files (x86)\Calibre2\calibre-debug.exe'


def main(*input_args):

    if not which(CALIBRE_PATH):
        input('No calibre (calibre-debug.exe) found!')
        return 0

    parser = argparse.ArgumentParser()
    parser.add_argument("filepath")
    parser.add_argument("-k", "--keep", action='store_true', help="keep temp and useless files")
    parser.add_argument("-z", "--compress", action='store_true', help="Compress the files")
    parser.add_argument("-p", "--pause-at-end", action='store_true', help="pause on error or finish")
    parser.add_argument("-o", "--output", help="choose save folder")
    args = parser.parse_args(input_args)

    p = Path(args.filepath)
    if not p.exists:
        print('Please provide a path to work on!')
        return 1

    print(f'Folder: {p}')

    azw_files = [f for f in p.iterdir() if (f.suffix.lower() in ['.azw', '.azw3'])]
    azw_files_DeDrmed = [f for f in p.iterdir() if f.name.lower().endswith('_nodrm.azw3')]

    deDRM = False
    if len(azw_files) == 0:
        errMsg = 'No .azw file found!'
        if args.pause_at_end:
            input(errMsg)
        else:
            print(errMsg)
        return 1
    elif len(azw_files_DeDrmed) == 1:
        deDRMed_azw_file = azw_files[0]
    elif len(azw_files) == 1:
        print(f'DeDRMing {azw_files[0].name}..')
        run(['py', '-2', DEDRM_PATH, azw_files[0]])
        temp_folder = p / 'temp'
        deDRMed_azw_file = next(f for f in p.iterdir() if f.name.endswith('_nodrm.azw3'))
        deDRM = True # this flags that the deDRMed file is created by ourselves (wasn't there before). So we remove it later.
    
    print(f'Extracting from {deDRMed_azw_file.name}..')
    run([CALIBRE_PATH, '-x', deDRMed_azw_file, temp_folder])
    if not args.keep:
        # Clean up `images` folder
        for f in (temp_folder / 'images').iterdir():
            if f.suffix.lower() in ['.unknown']:
                print(f'Removing {f}..')
                f.unlink()                
        imgs = [f for f in (temp_folder / 'images').iterdir() if f.suffix.lower() in ['.jpeg', '.jpg']]
        print(f'Removing {imgs[-1]}..')
        imgs[-1].unlink() # Remove the last image which is always a cover thumbnail.
        if deDRM:
            deDRMed_azw_file.unlink() # Remove deDRMed file.


    resFile = [f for f in p.iterdir() if (f.suffix.lower() in ['.res'])]

    if len(resFile) == 1:

        print(f'Processing resource file {resFile[0]}..')
        DumpAZW6_py3.main(['DumpAZW6_py3.py', str(resFile[0])])

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
    with (temp_folder / 'metadata.opf').open('r', encoding='utf8') as f:
        metadata = f.read()
    title = re.search(
        r'<dc:title>(.+?)</dc:title>', metadata, flags=re.DOTALL)[1].strip()

    for c in R'<>:"\/|?*' + '\r\n':  # Windows-safe filename
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

    if args.compress:
        zip_name = new_folder.with_name(new_folder.name + '.rar')
        run([R'C:\Program Files (x86)\WinRAR\Rar.exe', 'a', '-r', '-ep1', '-rr5p', '-m0',
             zip_name, str(new_folder) + "\\*"])
    
    if not args.keep:
        rmtree(temp_folder)
        if (p / 'azw6_images').exists():
            rmtree(p / 'azw6_images')

    if args.pause_at_end:
        input('All done!')


if __name__ == "__main__":
    args = sys.argv[1:]
    args.extend(['-o', 'G:\\','-z']) # 个人用
    main(*args)
