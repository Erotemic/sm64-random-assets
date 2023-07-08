#!/usr/bin/env python3
"""
Development helper script.  This populates the initial metadata information in
the repo.  It does not need to be run by an end user.
"""
import ubelt as ub
import aifc
import json
import kwimage


def main():
    """
    Given the .assets-local.txt file from a codebase with extracted assets
    determine the list of files that we will need to generate.
    """
    # Assumes running in the root of this repo
    # Given a set of pre-existing extracted assets
    input_dpath = ub.Path('~/code/sm64-port').expand()

    manifest_fpath = input_dpath / '.assets-local.txt'
    lines = manifest_fpath.read_text().split('\n')
    asset_fpaths = [ub.Path(p) for p in lines[2:-1]]

    asset_fpaths = [ub.Path(p) for p in lines[2:-1]]
    # Extract high level information about the file size and format of the file
    # we need to generate information for.

    metadata = []

    for fname in asset_fpaths:
        ext = fname.suffix
        if ext == '.aiff':
            info = parse_audio_info(input_dpath, fname)
            if info is not None:
                metadata.append(info)
            else:
                metadata.append({
                    'fname': str(fname),
                })
        elif ext == '.png':
            in_fpath = input_dpath / fname
            if in_fpath.exists():
                info = parse_image_info(input_dpath, fname)
                metadata.append(info)
            else:
                metadata.append({
                    'fname': str(fname),
                })
        elif ext == '.m64':
            # I have no idea what these files are. Zeroing them seems to work fine.
            in_fpath = input_dpath / fname
            if in_fpath.exists():
                orig = in_fpath.read_bytes()
                metadata.append({
                    'fname': str(fname),
                    'size': len(orig)
                })
            else:
                metadata.append({
                    'fname': str(fname),
                })
        elif ext == '.bin':
            # I have no idea what these files are. Zeroing them seems to work fine.
            in_fpath = input_dpath / fname
            if in_fpath.exists():
                orig = in_fpath.read_bytes()
                metadata.append({
                    'fname': str(fname),
                    'size': len(orig)
                })
            else:
                metadata.append({
                    'fname': str(fname),
                })

    metadata_text = json.dumps(metadata, indent='    ')
    print(metadata_text)

    # This repo path
    repo_dpath = ub.Path('~/code/sm64-random-assets').expand()
    # manifest_fpath.copy(repo_dpath, overwrite=True)

    asset_metadata_fpath = repo_dpath / 'asset_metadata.json'
    asset_metadata_fpath.write_text(metadata_text)


def parse_audio_info(input_dpath, fname):
    in_fpath = input_dpath / fname
    if not in_fpath.exists():
        return None
    file = aifc.open(open(in_fpath, 'rb'), 'rb')
    params = file.getparams()
    data = file.readframes(params.nframes)

    size = params.sampwidth * params.nframes
    assert len(data) == size

    param_dict = params._asdict()
    param_dict['compname'] = param_dict['compname'].decode('utf8')
    param_dict['comptype'] = param_dict['comptype'].decode('utf8')

    info = {
        'size': size,
        'params': param_dict,
        'fname': str(fname),
    }
    return info


def parse_image_info(input_dpath, fname):
    in_fpath = input_dpath / fname
    if not in_fpath.exists():
        return None

    shape = kwimage.load_image_shape(in_fpath)

    info = {
        'fname': str(fname),
        'shape': list(shape),
    }
    return info


if __name__ == '__main__':
    """
    CommandLine:
        python build_asset_metadata.py
    """
    main()
