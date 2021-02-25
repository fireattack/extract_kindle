import re
from subprocess import run
import sys
from shutil import rmtree, which, move
import DumpAZW6_py3
import argparse
from pathlib import Path


DEDRM_PATH = Path(__file__).parent / 'DeDRM_plugin'
CALIBRE_PATH = 'calibre-debug.exe' # Assuming in path already. Modify it to yours such as R'C:\Program Files (x86)\Calibre2\calibre-debug.exe'
RAR_PATH = R'C:\Program Files (x86)\WinRAR\Rar.exe' # Modify it to your Rar.exe. Or replace with 7z (but you also need to replace the arguments)
KEY = Path(__file__).parent / "kindlekey1.k4i"

def main(*input_args):

    if not which(CALIBRE_PATH):
        input('No calibre (calibre-debug.exe) found!')
        return 1

    has_rar = True
    if not which(RAR_PATH):
        input('No WinRAR (Rar.exe) found!')
        has_rar = True

    parser = argparse.ArgumentParser()
    parser.add_argument("filepath", help="choose the folder contains DRMed azw file(s)")
    parser.add_argument("-k", "--keep", action='store_true', help="keep temp and useless files")
    parser.add_argument("-z", "--compress", action='store_true', help="Also compress the files")
    parser.add_argument("-o", "--output", help="choose output folder")
    args = parser.parse_args(input_args)

    p = Path(args.filepath)
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
        deDRMed_azw_file = azw_files[0]
    elif len(azw_files) == 1:
        print(f'DeDRMing {azw_files[0].name}..')
        if not KEY.exists():
            run(['py', DEDRM_PATH / 'kindlekey.py', Path(__file__).parent])
        run(['py', DEDRM_PATH / 'k4mobidedrm.py', "-k", KEY, azw_files[0], p])
        if not KEY.exists():
            print('Failed to get key!')
            return 1
        #from DeDRM_plugin_modified.k4mobidedrm import decryptBook
        #decryptBook(azw_files[0], str(p), ['kindlekey1.k4i'], [], [], [])        
        deDRMed_azw_file = next(f for f in p.iterdir() if f.name.endswith('_nodrm.azw3'))
        deDRM = True # this flags that the deDRMed file is created by ourselves (wasn't there before). So we remove it later.
    
    print(f'Extracting from {deDRMed_azw_file.name}..')
    temp_folder = p / 'temp'
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
        run([RAR_PATH, 'a', '-r', '-ep1', '-rr5p', '-m0', zip_name, str(new_folder) + "\\*"])
    
    if not args.keep:
        rmtree(temp_folder)
        if (p / 'azw6_images').exists():
            rmtree(p / 'azw6_images')

    print('All done!')


if __name__ == "__main__":
    args = sys.argv[1:]
    main(*args)
