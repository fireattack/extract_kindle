import argparse
import json
import subprocess
import tempfile
import time
import traceback
import zipfile
from pathlib import Path

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
        for f in [
            Path('config.json'),
            Path(__file__).parent / 'config.json',
            Path.home() / '.extract_kindle_config.json'
        ]:
            if f.exists():
                config_file = f
                print(f"Using config file found: {config_file.resolve()}")
                break
        if not config_file:
            print(f"Config file {config_file} not found. Creating a default one...")
            config_file = Path('config.json')
            default_kindle_content_dir = Path.home() / 'Documents' / 'My Kindle Content'
            default_config = {
                'key_file': 'keys.txt',
                'dump_file': 'minidump',
                'kindle_content_dir': str(default_kindle_content_dir),
            }
            with config_file.open('w', encoding='utf8') as f:
                json.dump(default_config, f, indent=4)
            print(f"Created default config file at {config_file}")
            if not default_kindle_content_dir.exists():
                print(f'My Kindle Content folder not found at default path ({default_kindle_content_dir.resolve()}).'
                      '\nPlease manually set it in the config file and re-run the command.')
                quit(1)

        with config_file.open('r', encoding='utf8') as f:
            data = json.load(f)
        try:
            self.key_file = data['key_file']
            self.dump_file = data['dump_file']
            self.kindle_content_dir = data['kindle_content_dir']
            self.kindle_dir = data.get('kindle_dir') # this one is optional
        except KeyError as e:
            print(f"Missing key in config file: {e}. Please check the config file.")
            quit(1)

    def batch_decrypt(self, force=False):
        '''Decrypt all books in the My Kindle Content folder'''
        for folder in Path(self.kindle_content_dir).iterdir():
            if folder.name == 'NoteDocuments' or not folder.is_dir():
                continue
            if force:
                pass
            else:
                txt_fies = list(folder.glob("*.txt"))
                if len(txt_fies) == 1:
                    print(f'Skip already extracted: [{folder.name}] {txt_fies[0].stem}')
                    continue
            self.decrypt_book(folder)

    def decrypt_book(self, indir):
        indir = Path(indir)
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
            temp_zip = Path(f.name)
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
            temp_nodrm_file = temp_zip.with_name(temp_zip.stem + '_nodrm' + book.getBookExtension())
            book.getFile(temp_nodrm_file)
            print("Saved decrypted book {1:s} after {0:.1f} seconds".format(time.time()-starttime, temp_nodrm_file.name))
            book.cleanup()
        finally:
            try:
                temp_zip.unlink()
            except FileNotFoundError:
                pass
        _, outfile = convert_to_cbz(temp_nodrm_file, self.outdir)
        try:
            temp_nodrm_file.unlink()
        except FileNotFoundError:
            pass
        # create a empty text file in the dir to mark it as processed
        (indir / (outfile.stem + '.txt')).touch()

    def get_keys(self, dump_file=None):
        '''Get keys using KRFKeyExtractor.exe'''
        if dump_file is None:
            dump_file = self.dump_file
        kindle_dir = Path(self.kindle_dir) if self.kindle_dir else Path.home() / 'AppData/Local/Amazon/Kindle/application'
        KRFKeyExtractor = kindle_dir / 'KRFKeyExtractor.exe'
        if not KRFKeyExtractor.exists():
            raise(f"KRFKeyExtractor not found at {KRFKeyExtractor}.")
        process = subprocess.run([KRFKeyExtractor, dump_file, self.kindle_content_dir, self.key_file], stderr=subprocess.STDOUT, text=True)
        if process.returncode != 0:
            print(f"Error running KRFKeyExtractor:\n{process.stdout}")
            raise RuntimeError("KRFKeyExtractor failed")

        output = process.stdout.strip()
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
                print('Found the following minidump content:')
                print('-' * 20)
                print(minidump_content)
                print('-' * 20)
                with open(self.dump_file, 'w', encoding='utf-8') as f:
                    f.write(minidump_content)
                print(f"Save minidump to {self.dump_file}")
            else:
                raise('No valid minidump content found in the output. Something went wrong with KRFKeyExtractor. Please check the output:\n' + output)
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
    parser.add_argument('-f', '--force', action='store_true',
                        help='Force decryption even if the book is already decrypted')
    args = parser.parse_args()

    extractor = KindleExtractor(args.outdir)

    if args.command is None:
        print('Decrypting all the books in the My Kindle Content folder')
        extractor.get_keys()
        extractor.batch_decrypt(force=args.force)
    elif args.command == 'init':
        assert len(args.args) == 1, f"Usage: {Path(__file__).name} init <dumpfile>"
        extractor.get_keys(dump_file=args.args[0])
    else:
        indir = Path(args.command)
        extractor.get_keys()
        extractor.decrypt_book(indir)
