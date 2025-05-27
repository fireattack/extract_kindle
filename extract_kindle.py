import argparse
import os
import tempfile
import time
import traceback
import zipfile
from pathlib import Path
import subprocess
import json

from DeDRM_plugin.k4mobidedrm import GetDecryptedBook
from KFX_Input.kfxlib import YJ_Book


def sanitize(name):
    template = {'\\': '＼', '/': '／', ':': '：', '*': '＊', '?': '？', '"': '＂', '<': '＜', '>': '＞', '|': '｜', '\n': '', '\r': '', '\t': ''}
    for illegal in template:
        name = name.replace(illegal, template[illegal])
    return name


def convert_to_cbz(infile, outdir):
    book = YJ_Book(str(infile))
    book.decode_book(retain_yj_locals=True)
    book_title = book.get_yj_metadata_from_book().title
    print(f'Book title: {book_title}')
    outfile = Path(outdir) / sanitize(f'{book_title}.zip')
    if book.is_image_based_fixed_layout:
        cbz_data = book.convert_to_cbz()
        with outfile.open('wb') as f:
            f.write(cbz_data)
        print(f"Converted book images to CBZ file {outfile}")
        return book_title, outfile
    else:
        raise ("Book format does not support CBZ conversion - must be image based fixed-layout")


class KindleExtractor:
    def __init__(self, outdir='.'):
        self.outdir = Path(outdir)
        self._load_config()

    def _load_config(self):
        config_file = None
        for p in [
            Path(__file__).parent / 'config.json',
            Path('config.json'),
            self.outdir / 'config.json',
            Path.home() / '.extract_kindle_config.json'
        ]:
            if p.exists():
                config_file = Path(p)
                print(f"Using config file: {config_file}")
                break
        if not config_file.exists():
            config_file = Path.home() / '.extract_kindle_config.json'
            print(f"Config file {config_file} not found. Creating a default one...")
            default_config = {
                'key_file': 'keys.txt',
                'dump_file': 'minidump',
                'kindle_content_dir': str(Path.home() / 'Documents' / 'My Kindle Content'),
            }
            with config_file.open('w') as f:
                json.dump(default_config, f, indent=4)
            print(f"Created default config file at {config_file}")

        with config_file.open('r') as f:
            data = json.load(f)
            self.key_file = data.get('key_file', 'keys.txt')
            self.dump_file = data.get('dump_file', 'minidump')
            self.kindle_content_dir = data.get('kindle_content_dir')
            self.kindle_dir = data.get('kindle_dir') # this one is optional

    def batch_decrypt(self):
        '''Decrypt all books in the My Kindle Content folder'''
        for folder in Path(self.kindle_content_dir).iterdir():
            if folder.name == 'NoteDocuments' or not folder.is_dir():
                continue
            txt_fies = list(folder.glob("*.txt"))
            if len(txt_fies) == 1:
                print(f'Skip already extracted: [{folder.name}] {txt_fies[0].stem}')
                continue
            self.decrypt_book(folder)

    def decrypt_book(self, indir):
        indir = Path(indir)
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
            temp_zip = temp_zip.name
        try:
            with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file_path in indir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(indir)
                        zf.write(file_path, arcname)
            print(f"Created temporary zip: {temp_zip}")
            starttime = time.time()
            try:
                book = GetDecryptedBook(temp_zip, [], [], [], [], starttime, skeyfile=self.key_file)
            except Exception as e:
                print("Error decrypting book after {1:.1f} seconds: {0}".format(e.args[0], time.time()-starttime))
                traceback.print_exc()
                return 1
            infile_path = Path(temp_zip)
            temp_nodrm_file = infile_path.with_name(infile_path.stem + '_nodrm' + book.getBookExtension())
            book.getFile(temp_nodrm_file)
            print("Saved decrypted book {1:s} after {0:.1f} seconds".format(time.time()-starttime, temp_nodrm_file.name))
            book.cleanup()
        finally:
            try:
                os.unlink(temp_zip)
            except FileNotFoundError:
                pass
        _, outfile = convert_to_cbz(temp_nodrm_file, self.outdir)
        try:
            os.unlink(temp_nodrm_file)
        except FileNotFoundError:
            pass
        # create a empty text file in the dir to make it as processed
        (indir / (outfile.stem + '.txt')).touch()

    def get_keys(self, dump_file=None):
        '''Get keys using KRFKeyExtractor.exe'''
        if dump_file is None:
            dump_file = self.dump_file
        kindle_dir = Path(self.kindle_dir) if self.kindle_dir else Path.home() / 'AppData/Local/Amazon/Kindle/application'
        KRFKeyExtractor = kindle_dir / 'KRFKeyExtractor.exe'
        if not KRFKeyExtractor.exists():
            raise(f"KRFKeyExtractor not found at {KRFKeyExtractor}.")
        output = subprocess.check_output([KRFKeyExtractor, dump_file, self.kindle_content_dir, self.key_file],
                                         stderr=subprocess.STDOUT, text=True)
        if dump_file != self.dump_file:
            # If we're using the full dump, save the output to a minidump file for later use
            lines = output.split('\n')
            note_index = -1
            for i, line in enumerate(lines):
                if line.startswith("Note:"):
                    note_index = i
                    break
            if note_index != -1:
                minidump_content = '\n'.join(lines[note_index + 1:])
                with open(self.dump_file, 'w', encoding='utf-8') as f:
                    f.write(minidump_content)
                print(f"Save minidump to {self.dump_file}")
        print(f"Keys saved to {self.key_file}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Extracts and decrypts Kindle books.',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('command', nargs='?', metavar='COMMAND',
                        help='''Optional command to execute:
    (no command)       - Decrypt all books in 'My Kindle Content' folder.
    init <dumpfile>    - Initialize and save keys from a Kindle dump file. The <dumpfile> path is required.
    <book_folder_path> - Decrypt a specific book from its folder path.''')
    parser.add_argument('args', nargs='*', metavar='ARGUMENTS',
                        help='Additional arguments for the command (e.g., <dumpfile> for "init")')
    parser.add_argument('-O', '--outdir', default='.', metavar='DIRECTORY',
                        help='Output directory for decrypted books (default: current directory)')
    args = parser.parse_args()

    extractor = KindleExtractor(args.outdir)

    if args.command is None:
        print('Decrypting all the books in the My Kindle Content folder')
        extractor.get_keys()
        extractor.batch_decrypt()
    elif args.command == 'init':
        assert len(args.args) == 1, f"Usage: {Path(__file__).name} init <dumpfile>"
        extractor.get_keys(dump_file=args.args[0])
    else:
        indir = Path(args.command)
        extractor.get_keys()
        extractor.decrypt_book(indir)
