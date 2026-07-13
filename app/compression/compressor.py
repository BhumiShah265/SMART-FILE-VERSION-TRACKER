import zipfile

def compress_file(file_bytes, destination_path, arcname):
    with zipfile.ZipFile(destination_path,'w',zipfile.ZIP_DEFLATEd) as zf:
        zf.writestr(arcname,file_bytes)

def compress_fole(zip_path,arcname):
    with zipfile.ZipFile(zip_path,'r') as zf:
        return zf.read(arcname)