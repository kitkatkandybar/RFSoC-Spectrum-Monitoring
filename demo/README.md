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

## Running the Demo

Open up GNURadio Companion. In gnuradio companion open up painttest.grc. Fill out the grc file to have the correct settings, e.g. pluto usb location and the name of the bin file. The file needs to be a binary file to work properly but you can change most image files into binary files easily. Run the GRC file with a pluto that has a TX antenna and see if the image pops up.
