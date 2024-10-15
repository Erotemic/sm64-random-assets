from sm64_random_assets.util import util_random


def generate_audio(output_dpath, info):
    """
    Generates a valid audio file based on info and writes it to disk.

    Args:
        output_path (str | PathLike):

        info (dict): contains parameters for how data should be generated

    Returns:
        Dict: metadata containing status
    """
    from sm64_random_assets.vendor import aifc
    if info.get('params', None) is None:
        return {'status': 'value-error: audio has no params'}
    params_dict = info['params'].copy()
    params_dict['comptype'] = params_dict['comptype'].encode()
    params_dict['compname'] = params_dict['compname'].encode()
    params = aifc._aifc_params(**params_dict)

    # Seed the rng based on the filename to get some determinism for debugging
    rng = util_random.ensure_rng(info['fname'])

    if info['use_ref'] == 'zero':
        # Zero out all sounds
        new_data = b'\x00' * info['size']
        out = {'status': 'zeroed'}
    else:
        import numpy as np
        # Random new sound (this works surprisingly well)
        # n_consecutive = 256  # todo: parameterize
        n_consecutive = 1
        # Make a bit less random so it can be compressed
        size = params.nframes * params.nchannels
        samples = rng.randint(-32768, 32767, size, dtype=np.int16)
        for i in range(0, len(samples), n_consecutive):
            value = samples[i]
            samples[i:i + n_consecutive] = value
        new_data = samples.tobytes()
        out = {'status': 'randomized'}

    out_fpath = output_dpath / info['fname']
    out_fpath.parent.ensuredir()

    with open(out_fpath, 'wb') as file:
        new_file = aifc.open(file, 'wb')
        new_file.setparams(params)
        new_file.writeframes(new_data)

    return out
