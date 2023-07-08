Jonathan Crall

    Is there an existing nix package that provides the mips-binutils toolchain? (Similar to apt install binutils-mips-linux-gnu)?

Zhaofeng Li

    Try pkgsCross.mipsel-linux-gnu.buildPackages.bintools (and mips-linux-gnu as well)

Jonathan Crall

    If those don't how up on https://search.nixos.org/packages do they not exist?

Zhaofeng Li

    pkgsCross is special as it's just a shortcut to cross-compile packages (e.g., pkgsCross.aarch64-multiplatform.hello), the search would be very cluttered if those are there

    But I suppose there is a better way to surface discoverability for them (there are manually-added aliases in all-packages.nix to some ARM tools IIRC)


Jonathan Crall

    Ok, cool. That seems to be getting me somewhere. (I'm very new to NixOS and using Replit, which I hope doesn't matter). I've added pkgs.pkgsCross.mipsel-linux-gnu.buildPackages.bintools to my deps list in the replit.nix config and opened a new shell. I was able to see the executables: mipsel-unknown-linux-gnu-ld, mipsel-unknown-linux-gnu-objdump, etc...

    When I added pkgs.mips-linux-gnu to that deps list, it gave an error when I opened a new shell saying mips-linux-gnu is missing.

    Not sure that I'm requesting the packages correctly (please say so if I'm not), but I think the fact that I got something is a good sign.


Zhaofeng Li

It should be
pkgs.pkgsCross.mips-linux-gnu with the pkgsCross in there. Other valid attributes are here: https://github.com/NixOS/nixpkgs/blob/d6784f25a2c0ee72d83e6783061c52b1c9254aa8/lib/systems/examples.nix#L93-L95

To elaborate a bit further, you can actually "make your own" when initializing the package set if the examples aren't enough:

.. code::

    armPkgs = import pkgs.path {
      crossSystem = "aarch64-linux";...
    };

With this, armPkgs.hello and armPkgs.gcc will be GNU Hello and GCC built to run on ARM64 Linux, whereas armPkgs.buildPackages.gcc will be GCC built to run on your own platform but produce code for ARM64 Linux
(but you typically want to use stdenv.cc instead of gcc for more composability)


https://github.com/NixOS/nixpkgs/blob/d6784f25a2c0ee72d83e6783061c52b1c9254aa8/lib/systems/examples.nix#L93-L95



Jonathan Crall

Thank you this is extremely helpful. I think I need to learn more about what the .nix configuration files are doing because it seems more powerful than I originally thought it was.

For context I'm trying to build code that will run on an old MIPS R4000 Processor (the chip on the N64), specifically the m64 decomp, which has a Makefile looking for the following tools:

    # detect prefix for MIPS toolchain
    ifneq      ($(call find-command,mips-linux-gnu-ld),)
      CROSS := mips-linux-gnu-
    else ifneq ($(call find-command,mips64-linux-gnu-ld),)
      CROSS := mips64-linux-gnu-
    else ifneq ($(call find-command,mips64-elf-ld),)
      CROSS := mips64-elf-
    else
      $(error Unable to detect a suitable MIPS toolchain installed)
    endif

I think using your instructions I may be able to cobble something together.



Zhaofeng Li


I'm not sure what the replit config is supposed to look like, is it like a mkShell?


Jonathan Crall


Right now it looks like this:


.. code::


  { pkgs }: {
  deps = [
    pkgs.python310Full
    pkgs.replitPackages.prybar-python310
    pkgs.replitPackages.stderred
    pkgs.capstone
    pkgs.pkg-config
    pkgs.python310Packages.pkgconfig
    pkgs.binutils
    #pkgs.pkgsCross.mips-linux-gnu
    pkgs.pkgsCross.mipsel-linux-gnu.buildPackages.bintools
    #pkgs.pkgsCross.mips-linux-gnu.buildPackages.bintools
  ];
  env = {
    PYTHON_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      # Needed for pandas / numpy
      pkgs.stdenv.cc.cc.lib
      pkgs.zlib
      # Needed for pygame
      pkgs.glib
      # Needed for matplotlib
      pkgs.xorg.libX11
    ];
    PYTHONHOME = "${pkgs.python310Full}";
    PYTHONBIN = "${pkgs.python310Full}/bin/python3.10";
    LANG = "en_US.UTF-8";
    STDERREDBIN = "${pkgs.replitPackages.stderred}/bin/stderred";
    PRYBAR_PYTHON_BIN = "${pkgs.replitPackages.prybar-python310}/bin/prybar-python310";
  };
}


I commented out lines that produced errors when it reloaded the environment, so I'm guessing / checking right now.
But pkgs.pkgsCross.mipsel-linux-gnu.buildPackages.bintools definately did something and gave me tools I didn't have before.


Zhaofeng Li


Hmm, I immediately don't see a way to override a stdenv, but for a normal shell.nix, you typically want something like

.. code::

    mkShell = pkgs.mkShell.override { stdenv = pkgs.pkgsCross.mips-linux-gnu.stdenv; };


In such an environment, variables like $CC and $CXX will be set correctly for
MIPS, as well as other things like nativeBuildInput/buildInput resolution


Jon:

    Hmm, it seems like Replit might not be exposing a full nix configuration? After reading a bit I think I can create my own shell.nix and then run nix-shell to get the appropriate environment.


adisbladis :

    Use pythonX.withPackages to construct your python envs





{ pkgs ? import <nixpkgs> {} # here we import the nixpkgs package set
}:
pkgs.mkShell {               # mkShell is a helper function
  name="dev-environment";    # that requires a name
  buildInputs = [            # and a list of packages
    pkgs.nodejs
  ];
  shellHook = ''             # bash to run when you enter the shell
    echo "Start developing..."
   '';
}



LETS LEARN HOW TO NIX:
======================

let / with - https://nixos.org/guides/nix-pills/basics-of-language.html

override - https://nixos.org/guides/nix-pills/override-design-pattern.html
