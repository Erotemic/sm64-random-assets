
def generate_binary(output_dpath, info):
    """
    Generates a binary file

    Args:
        output_path (str | PathLike):

        info (dict):

    Returns:
        Dict: metadata containing status
    """
    if info.get('size', None) is None:
        return {'status': 'value-error: binary has no size'}
    out_fpath = output_dpath / info['fname']
    out_fpath.parent.ensuredir()
    # Not sure what these bin/m64 file are. Zeroing them seems to work fine.
    # Note: the m64 are music files. Still dont know what bin file are.
    new = b'\x00' * info['size']
    out_fpath.write_bytes(new)
    out = {'status': 'zeroed'}
    return out
