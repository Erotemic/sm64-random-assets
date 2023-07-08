
def generate_binary(output_dpath, info):
    if info.get('size', None) is None:
        return {'status': 'value-error: binary has no size'}
    out_fpath = output_dpath / info['fname']
    out_fpath.parent.ensuredir()
    # Not sure what these bin/m64 file are. Zeroing them seems to work fine.
    new = b'\x00' * info['size']
    out_fpath.write_bytes(new)
    out = {'status': 'zeroed'}
    return out
