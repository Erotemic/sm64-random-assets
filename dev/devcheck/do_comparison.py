"""
Hacky script to help with comparison
"""
import ubelt as ub
# import sm64_random_assets
# Path to the random asset repo
repo_dpath = ub.Path('~/code/sm64-random-assets').expanduser()

ub.cmd('git submodule update --init tpl/sm64', cwd=repo_dpath, verbose=3)
ub.cmd('git clone sm64/.git sm64-ref', cwd=repo_dpath / 'tpl', verbose=3)

reference_dpath = (repo_dpath / 'tpl/sm64-ref')

cand = repo_dpath / 'baserom.us.z64'
if cand.exists():
    base_rom_fpath = cand

new_base_rom_fpath = reference_dpath / base_rom_fpath.name
if not list(reference_dpath.glob('baserom')):
    base_rom_fpath.copy(new_base_rom_fpath)
assert new_base_rom_fpath.exists()

# Just call the extract script in the repo
ub.cmd('python extract_assets.py us', cwd=reference_dpath)

"""

Now we can generate with references


python $HOME/code/sm64-random-assets/generate_assets.py \
    --dst $HOME/code/sm64-random-assets/tpl/sm64-port \
    --reference $HOME/code/sm64-random-assets/tpl/sm64-ref \
    --compare

"""
