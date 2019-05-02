#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai

import sys

import os, getopt, struct
import imghdr

def get_image_type(imgname, imgdata=None):
    imgtype = imghdr.what(imgname, imgdata)

    # horrible hack since imghdr detects jxr/wdp as tiffs
    if imgtype is not None and imgtype == "tiff":
        imgtype = "wdp"

    # imghdr only checks for JFIF or Exif JPEG files. Apparently, there are some
    # with only the magic JPEG bytes out there...
    # ImageMagick handles those, so, do it too.
    if imgtype is None:
        if imgdata[0:2] == b'\xFF\xD8':
            # Get last non-null bytes
            last = len(imgdata)
            while (imgdata[last-1:last] == b'\x00'):
                last-=1
            # Be extra safe, check the trailing bytes, too.
            if imgdata[last-2:last] == b'\xFF\xD9':
                imgtype = "jpeg"
    return imgtype


def processCRES(i, data):
    data = data[12:]
    imgtype = get_image_type(None, data)
    if imgtype is None:
        print("        Warning: CRES Section %s does not contain a recognised resource" % i)
        imgtype = "dat"
    imgname = "HDimage%05d.%s" % (i, imgtype)
    imgdir = os.path.join(".", "azw6_images")
    if not os.path.exists(imgdir):
        os.mkdir(imgdir)
    print("        Extracting HD image: {0:s} from section {1:d}".format(imgname,i))
    imgpath = os.path.join(imgdir, imgname)
    with open(imgpath, 'wb') as f:
        f.write(data) 
    return

# this is just guesswork so far, making big assumption that 
# metavalue key numbers reamin the same in the CONT EXTH
def dump_contexth(codec, extheader):
    
    # determine text encoding
    if extheader == '':
        return
    id_map_strings = {
           1 : 'Drm Server Id (1)',
           2 : 'Drm Commerce Id (2)',
           3 : 'Drm Ebookbase Book Id(3)',
           100 : 'Creator_(100)',
           101 : 'Publisher_(101)',
           102 : 'Imprint_(102)',
           103 : 'Description_(103)',
           104 : 'ISBN_(104)',
           105 : 'Subject_(105)',
           106 : 'Published_(106)',
           107 : 'Review_(107)',
           108 : 'Contributor_(108)',
           109 : 'Rights_(109)',
           110 : 'SubjectCode_(110)',
           111 : 'Type_(111)',
           112 : 'Source_(112)',
           113 : 'ASIN_(113)',
           114 : 'versionNumber_(114)',
           117 : 'Adult_(117)',
           118 : 'Price_(118)',
           119 : 'Currency_(119)',
           122 : 'fixed-layout_(122)',
           123 : 'book-type_(123)',
           124 : 'orientation-lock_(124)',
           126 : 'original-resolution_(126)',
           127 : 'zero-gutter_(127)',
           128 : 'zero-margin_(128)',
           129 : 'K8_Masthead/Cover_Image_(129)',
           132 : 'RegionMagnification_(132)',
           200 : 'DictShortName_(200)',
           208 : 'Watermark_(208)',
           501 : 'cdeType_(501)',
           502 : 'last_update_time_(502)',
           503 : 'Updated_Title_(503)',
           504 : 'ASIN_(504)',
           508 : 'Unknown_Title_Furigana?_(508)',
           517 : 'Unknown_Creator_Furigana?_(517)',
           522 : 'Unknown_Publisher_Furigana?_(522)',
           524 : 'Language_(524)',
           525 : 'primary-writing-mode_(525)',
           526 : 'Unknown_(526)',
           527 : 'page-progression-direction_(527)',
           528 : 'override-kindle_fonts_(528)',
           529 : 'Unknown_(529)',
           534 : 'Input_Source_Type_(534)',
           535 : 'Kindlegen_BuildRev_Number_(535)',
           536 : 'Container_Info_(536)', # CONT_Header is 0, Ends with CONTAINER_BOUNDARY (or Asset_Type?)
           538 : 'Container_Resolution_(538)',
           539 : 'Container_Mimetype_(539)',
           542 : 'Unknown_but_changes_with_filename_only_(542)',
           543 : 'Container_id_(543)',  # FONT_CONTAINER, BW_CONTAINER, HD_CONTAINER
           544 : 'Unknown_(544)',
    }
    id_map_values = {
           115 : 'sample_(115)',
           116 : 'StartOffset_(116)',
           121 : 'K8(121)_Boundary_Section_(121)',
           125 : 'K8_Count_of_Resources_Fonts_Images_(125)',
           131 : 'K8_Unidentified_Count_(131)',
           201 : 'CoverOffset_(201)',
           202 : 'ThumbOffset_(202)',
           203 : 'Fake_Cover_(203)',
           204 : 'Creator_Software_(204)',
           205 : 'Creator_Major_Version_(205)',
           206 : 'Creator_Minor_Version_(206)',
           207 : 'Creator_Build_Number_(207)',
           401 : 'Clipping_Limit_(401)',
           402 : 'Publisher_Limit_(402)',
           404 : 'Text_to_Speech_Disabled_(404)',
    }
    id_map_hexstrings = {
           209 : 'Tamper_Proof_Keys_(209_in_hex)',
           300 : 'Font_Signature_(300_in_hex)',
    }
    _length, num_items = struct.unpack('>LL', extheader[4:12])
    extheader = extheader[12:]
    pos = 0

    for _ in range(num_items):
        id, size = struct.unpack('>LL', extheader[pos:pos+8])
        content = extheader[pos + 8: pos + size]
        if id in list(id_map_strings.keys()):
            name = id_map_strings[id]
            print('\n    Key: "%s"\n        Value: "%s"' % (name, str(content, codec)))
        elif id in list(id_map_values.keys()):
            name = id_map_values[id]
            if size == 9:
                value, = struct.unpack('B',content)
                print('\n    Key: "%s"\n        Value: 0x%01x' % (name, value))
            elif size == 10:
                value, = struct.unpack('>H',content)
                print('\n    Key: "%s"\n        Value: 0x%02x' % (name, value))
            elif size == 12:
                value, = struct.unpack('>L',content)
                print('\n    Key: "%s"\n        Value: 0x%04x' % (name, value))
            else:
                print("\nError: Value for %s has unexpected size of %s" % (name, size))
        elif id in list(id_map_hexstrings.keys()):
            name = id_map_hexstrings[id]
            print('\n    Key: "%s"\n        Value: 0x%s' % (name, content.hex()))
        else:
            print("\nWarning: Unknown metadata with id %s found" % id)
            name = str(id) + ' (hex)'
            print('    Key: "%s"\n        Value: 0x%s' % (name, content.hex()))
        pos += size
    return


def sortedHeaderKeys(mheader):
    hdrkeys = sorted(list(mheader.keys()), key=lambda akey: mheader[akey][0])
    return hdrkeys


class dumpHeaderException(Exception):
    pass

class PalmDB:
    # important  palmdb header offsets
    unique_id_seed = 68
    number_of_pdb_records = 76
    first_pdb_record = 78

    def __init__(self, palmdata):
        self.data = palmdata
        self.nsec, = struct.unpack_from('>H',self.data,PalmDB.number_of_pdb_records)

    def getsecaddr(self,secno):
        secstart, = struct.unpack_from('>L', self.data, PalmDB.first_pdb_record+secno*8)
        if secno == self.nsec-1:
            secend = len(self.data)
        else:
            secend, = struct.unpack_from('>L',self.data,PalmDB.first_pdb_record+(secno+1)*8)
        return secstart,secend

    def readsection(self,secno):
        if secno < self.nsec:
            secstart, secend = self.getsecaddr(secno)
            return self.data[secstart:secend]
        return ''

    def getnumsections(self):
        return self.nsec


class HdrParser:
    cont_header = {
            'magic'               : (0x00, '4s', 4),
            'record_size'         : (0x04, '>L', 4),
            'type'                : (0x08, '>H', 2),
            'count'               : (0x0A, '>H', 2),
            'codepage'            : (0x0C, '>L', 4),
            'unknown0'            : (0x10, '>L', 4),
            'unknown1'            : (0x14, '>L', 4),
            'num_resc_recs'       : (0x18, '>L', 4),
            'num_wo_placeholders' : (0x1C, '>L', 4),
            'offset_to_hrefs'     : (0x20, '>L', 4),
            'unknown2'            : (0x24, '>L', 4),
            'title_offset'        : (0x28, '>L', 4),
            'title_length'        : (0x2C, '>L', 4),
    }

    cont_header_sorted_keys = sortedHeaderKeys(cont_header)

    def __init__(self, header, start):
        self.header = header
        self.start = start
        self.hdr = {}
        # set it up for the proper header version
        self.header_sorted_keys = HdrParser.cont_header_sorted_keys
        self.cont_header = HdrParser.cont_header

        # parse the header information
        for key in self.header_sorted_keys:
            (pos, format, tot_len) = self.cont_header[key]
            if pos < 48:
                val, = struct.unpack_from(format, self.header, pos)
                self.hdr[key] = val
        self.exth = self.header[48:]
        self.title_offset = self.hdr['title_offset']
        self.title_length = self.hdr['title_length']
        self.title = self.header[self.title_offset: self.title_offset + self.title_length]
        self.codec = 'windows-1252'
        self.codec_map = {
            1252 : 'windows-1252',
            65001: 'utf-8',
            }
        if self.hdr['codepage'] in list(self.codec_map.keys()):
            self.codec = self.codec_map[self.hdr['codepage']]
        self.title = self.title.decode(self.codec)

    def dumpHeaderInfo(self):
        for key in self.cont_header_sorted_keys:
            (pos, format, tot_len) = self.cont_header[key]
            if pos < 48:
                if key == 'magic':
                    print("  Field: %20s   Offset: 0x%03x   Width:  %d   Value: %s" % (key, pos, tot_len, self.hdr[key].decode()))
                else:
                    print(("  Field: %20s   Offset: 0x%03x   Width:  %d   Value: 0x%0" + str(tot_len) + "x") % (key, pos, tot_len, self.hdr[key]))
                
        print("EXTH Region Length:  0x%0x" % len(self.exth))
        print("EXTH MetaData")

        #print(f'stdin: {sys.stdin.encoding}, stdout: {sys.stdout.encoding}')
        try: 
            print(self.title)
        except: # It will have problem otherwise in certain env, such as when redirect output to '> 1.txt'            
            print(self.title.encode(sys.stdout.encoding, "ignore").decode(sys.stdout.encoding))
        
        dump_contexth(self.codec, self.exth)
        return

def usage(progname):
    print("")
    print("Description:")
    print("   Dump the image from an AZW6 HD container file")
    print("  ")
    print("Usage:")
    print("  %s -h infile.azw6" % progname)
    print("  ")
    print("Options:")
    print("    -h           print this help message")


def main(argv=sys.argv):
    print("DumpAZW6 v01")
    progname = os.path.basename(argv[0])
    try:
        opts, args = getopt.getopt(argv[1:], "h")
    except getopt.GetoptError as err:
        print(str(err))
        usage(progname)
        sys.exit(2)
    
    if len(args) != 1:
        usage(progname)
        sys.exit(2)

    for o, a in opts:
        if o == "-h":
            usage(progname)
            sys.exit(0)

    infile = args[0]
    infileext = os.path.splitext(infile)[1].upper()
    print(infile, infileext)
    if infileext not in ['.AZW6','.RES']:
        print("Error: first parameter must be a Kindle AZW6 HD container file.")
        return 1

    try:
        # make sure it is really an hd container file
        contdata = open(infile, 'rb').read()
        palmheader = contdata[0:78]
        ident = palmheader[0x3C:0x3C+8]
        if ident != b'RBINCONT':
            raise dumpHeaderException('invalid file format')

        headers = {}

        pp = PalmDB(contdata)
        header = pp.readsection(0)

        print("\n\nFirst Header Dump from Section %d" % 0)
        hp = HdrParser(header, 0)
        hp.dumpHeaderInfo()

        # now dump a basic sector map of the palmdb
        n = pp.getnumsections()
        dtmap = {
            b"FONT": "FONT",
            b"RESC": "RESC",
            b"CRES": "CRES",
            b"CONT": "CONT",
            b'\xa0\xa0\xa0\xa0': "Empty_Image/Resource_Placeholder",
            b'\xe9\x8e\r\n': "EOF_RECORD",
            }
        dtmap2 = {
            b"kindle:embed" : "KINDLE:EMBED",
        }
        tr = -1
        off = -1
        hp = None
        secmap = {}
        print("\nMap of Palm DB Sections")
        print("    Dec  - Hex : Description")
        print("    ---- - ----  -----------")
        for i in range(n):
            before, after = pp.getsecaddr(i)
            data = pp.readsection(i)
            dlen = len(data)
            dt = data[0:4]            
            dtext = data[0:12]
            desc = '' 
            if dtext in list(dtmap2.keys()):
                desc = data.decode()
                linkhrefs = []
                hreflist = desc.split('|')
                for href in hreflist:
                    if href != "":
                        linkhrefs.append("        " +   href)
                desc = "\n" + "\n".join(linkhrefs)
            elif dt in list(dtmap.keys()):
                desc = dtmap[dt]
                if dt == b"CONT":
                    desc="Cont Header"
                elif dt == b"CRES":
                    processCRES(i, data)
            else:
                desc = dtext.hex()
                desc = desc + " " + dtext.decode()
            if desc != "CONT":
                print("    %04d - %04x: %s [%d]" % (i, i, desc, dlen))

    except Exception as e:
        print("Error: %s" % e)
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
