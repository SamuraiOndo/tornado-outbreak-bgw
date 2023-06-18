
from binary_reader import BinaryReader
import sys
from pathlib import Path
import os
import zlib
import json
Mypath = Path(sys.argv[1])
directory = str(Mypath.resolve().parent)
Myfilename = Mypath.name
w = BinaryReader()
w.set_endian(False)
isFile = os.path.isfile(sys.argv[1])
unique_id = 0
if(Mypath.is_file()):
    path = Mypath.open("rb")
    reader = BinaryReader(path.read())
    reader.set_endian(True)
    if (reader.read_str(4) == "ZLIB"):
        unk2 = reader.read_uint32()
        path.seek(8)
        data = zlib.decompress(path.read())
        reader = BinaryReader(data)
        print("ZLIB compressed, decompressing...")
    reader.set_endian(True) # little endian
    reader.seek(0x00)
    unk = reader.read_uint32()
    filecount = reader.read_uint32()
    header = {
        "Unk 1": unk,
        "Count": filecount,
    }
    p = 0
    for i in range(filecount):
        type = reader.read_uint32()
        size = reader.read_uint32()
        file = reader.read_bytes(size)
        readertemp = BinaryReader(file)
        #stole from retraso hello!!
        try: #Yes, this is a terrible way of doing this
            try:
                readertemp.seek(8)
                newfile_magic = readertemp.read_str(4)
                if (len(newfile_magic) == 4):
                    magic_is_bad = any(not c.isalnum() for c in newfile_magic)
                    if magic_is_bad:
                        raise Exception("bad 4 char magic")
                else:
                    raise Exception("magic length less than 4")
            except:
                readertemp.seek(20)
                newfile_magic = readertemp.read_str(4)
                if (len(newfile_magic) == 4):
                    magic_is_bad = any(not c.isalnum() for c in newfile_magic)
                    if magic_is_bad:
                        raise Exception("bad 4 char magic")
                else:
                    raise Exception("magic length less than 4")
        except:
            newfile_magic = "dat" #Default extension
        filename = str(i) + "." + newfile_magic
        oldfilename = filename
        #attempting to get file names
        if (type == 7):
            try:
                readertemp.seek(29)
                filename = readertemp.read_str()
            except:
                pass
        elif(type == 2):
            try:
                readertemp.seek(10)
                filename = readertemp.read_str()
                if (filename == ""):
                    readertemp.seek(16)
                    filename = readertemp.read_str()
            except:
                pass
            
        
        output_path = directory / Path(Myfilename + ".unpack")
        output_path.mkdir(parents=True, exist_ok=True)
        filename = filename.replace("|",".")
        try:
            output_file = output_path / (filename)
            if not os.path.exists(output_file):
                fe = open(output_file, "wb")
                fe.write(file)
            else:
                raise Exception("File Exists")
        except:
            filename = oldfilename
            output_file = output_path / (filename)
            fe = open(output_file, "wb")
            fe.write(file)
        fileForJson = {
                    "Type": type,
                    "File Name": filename,
                }
        print(f"Saving {filename}...")
        header.update({p: fileForJson})
        p+=1
        fe.close()
    output_file = Path(sys.argv[1] + ".unpack") / ("manifest.json")
    filejson = open(output_file, "w")
    filejson.write(json.dumps(header,ensure_ascii = False, indent = 2))
    filejson.close()
else:
    f = open((sys.argv[1] + "/manifest.json"), "r")
    p = json.loads(f.read())
    fe = open(sys.argv[1].replace(".unpack",""),"wb")
    w = BinaryReader()
    w.set_endian(True)
    w.write_uint32(p["Unk 1"])
    w.write_uint32(p["Count"])
    for i in range(int(p["Count"])):
        w.write_uint32(p[str(i)]["Type"])
        file = Path(sys.argv[1]) / p[str(i)]["File Name"]
        print(f"Loading {file}...")
        fb = open(file, "rb")
        w.write_uint32(os.path.getsize(file))
        w.write_bytes(fb.read())
        fb.close()
    w.write_uint8(0)
    zlibw = BinaryReader()
    zlibw.set_endian(True)
    zlibw.write_str_fixed("ZLIB",4)
    zlibw.write_uint32(len(w.buffer()))
    print(f"Compressing file into ZLIB format...")
    zlibw.write_bytes(zlib.compress(w.buffer(),9)) #this is the ONLY type of compression the game excepts, the highest level
    fe.write(zlibw.buffer())
        
