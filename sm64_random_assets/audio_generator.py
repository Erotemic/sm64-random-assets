import os


def generate_audio(output_dpath, info):
    from sm64_random_assets.vendor import aifc
    if info.get('params', None) is None:
        return {'status': 'value-error: audio has no params'}
    params_dict = info['params'].copy()
    params_dict['comptype'] = params_dict['comptype'].encode()
    params_dict['compname'] = params_dict['compname'].encode()
    params = aifc._aifc_params(**params_dict)

    # Random new sound (this works surprisingly well)
    new_data = os.urandom(info['size'])

    # Zero out all sounds
    # new_data = b'\x00' * len(data)

    out_fpath = output_dpath / info['fname']
    out_fpath.parent.ensuredir()

    with open(out_fpath, 'wb') as file:
        new_file = aifc.open(file, 'wb')
        new_file.setparams(params)
        new_file.writeframes(new_data)

    # out = {'status': 'zeroed'}
    out = {'status': 'randomized'}
    return out
