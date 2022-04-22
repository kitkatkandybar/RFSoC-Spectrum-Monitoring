# Demo

This demo will use GNURadio to send out a signal which can then be viewed on the RFSoC.

## Demo Set up

First install [Anaconda](https://docs.anaconda.com/anaconda/install/index.html) and [GNURadio](https://www.gnuradio.org/) using the instructions [here](https://wiki.gnuradio.org/index.php/CondaInstall). The user should also make sure to  follow the steps in the section on building [out of tree modules (OOT)](https://wiki.gnuradio.org/index.php/CondaInstall#Building_OOT_modules_to_use_with_conda-installed_GNU_Radio). Next up install [gr-paint](https://github.com/drmpeg/gr-paint) by first downloading the GitHub repository and using the command line to go into the directory. Then if they are using linux or mac they should use the following:

```bash
mkdir build
cd build
cmake -G Ninja -DCMAKE_INSTALL_PREFIX=$CONDA_PREFIX -DCMAKE_PREFIX_PATH=$CONDA_PREFIX -DLIB_SUFFIX="" ..
make
make install
ldconfig
```

Windows users will have to make a slight change to the cmake line. Again follow the instructions in the [OOT install section](https://wiki.gnuradio.org/index.php/CondaInstall#Building_OOT_modules_to_use_with_conda-installed_GNU_Radio).

## Making an image so this works
There are instructions in the readme of [gr-paint](https://github.com/drmpeg/gr-paint) but here's the basic part.

First go to the grpaint directory and build the tgatoluma.c file that in the base directory. Here's the linux/macos way to do it.

```bash
gcc -o tgatoluma tgatoluma.c
```

Next install [ImageMagick](https://imagemagick.org/script/index.php). Once installed you can run commands to convert the files. First create at tga file.

```bash
convert <imagename.png> <imagename.tga>
./tgatoluma <imagename.tga> <imagename.bin>
```



## Running the Demo

Open up GNURadio Companion. In gnuradio companion open up painttest.grc. Fill out the grc file to have the correct settings, e.g. pluto usb location and the name of the bin file. The file needs to be a binary file to work properly but you can change most image files into binary files easily. Run the GRC file with a pluto that has a TX antenna and see if the image pops up.
