# https://en.wikibooks.org/wiki/N64_Programming/Compiling
# https://www.moria.us/blog/2020/10/n64-part1-land-of-pain
sudo apt install libmpc-dev

mkdir -p "$HOME"/tmp/n64tools
cd "$HOME"/tmp/n64tools

#curl -O https://ftp.gnu.org/gnu/binutils/binutils-2.27.tar.gz
#curl -O https://ftp.gnu.org/gnu/gcc/gcc-6.3.0/gcc-6.3.0.tar.gz

#tar -xvf binutils-2.27.tar.gz
#tar -xvf gcc-6.3.0.tar.gz

#rm -rf gcc-6.3.0.tar binutils-2.27.tar

#cd binutils-2.27
#export DIR="$HOME"/tmp/build-gcc/output
#export GCC=gcc
#./configure --target=mips64 --prefix=$DIR --program-prefix=mips64- --with-cpu=mips64vr4300
#make CC=$GCC -j16
#make install
#cd ..



#cd gcc-6.3.0
#export DIR="$HOME"/tmp/build-gcc/output
#export GCC=gcc
#export PATH=$PATH:$DIR/bin
## Requires patch: https://github.com/crosstool-ng/crosstool-ng/issues/992
#sed -i "s|xloc.file == '|xloc.file[0] == '|g" gcc/ubsan.c
#./configure --target=mips64 --prefix=$DIR --program-prefix=mips64- --with-arch=mips64vr4300 -with-languages=c --disable-threads
#make CC=$GCC -j16
#make install


curl -O https://ftp.gnu.org/gnu/binutils/binutils-2.35.1.tar.gz
curl -O https://ftp.gnu.org/gnu/gcc/gcc-10.2.0/gcc-10.2.0.tar.gz
tar -xvf binutils-2.35.1.tar.gz
tar -xvf gcc-10.2.0.tar.gz

PREFIX="$HOME"/tmp/n64tools/n64
mkdir -p $PREFIX

PATH=$PREFIX/bin:$PATH

mkdir -p build-binutils
cd build-binutils
../binutils-2.35.1/configure \
  --target=mips64-elf --prefix=$PREFIX \
  --program-prefix=mips64- --with-cpu=vr4300 \
  --with-sysroot --disable-nls --disable-werror
make -j16
make install
cd ..


mkdir -p build-gcc
cd build-gcc
../gcc-10.2.0/configure \
  --target=mips64-elf --prefix=$PREFIX \
  --program-prefix=mips64- --with-arch=vr4300 \
  -with-languages=c,c++ --disable-threads \
  --disable-nls --without-headers
make all-gcc -j16
make all-target-libgcc -j16
make install-gcc
make install-target-libgcc
