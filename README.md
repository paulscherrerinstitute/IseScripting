# General Information

## Maintainer
Jonas Purtschert [jonas.purtschert@psi.ch]

## Author
Oliver Bründler [oliver.bruendler@psi.ch]

## License
This library is published under [PSI HDL Library License](License.txt), which is [LGPL](LGPL2_1.txt) plus some additional exceptions to clarify the LGPL terms in the context of firmware development.

## Changelog
See [Changelog](Changelog.md)

## What belongs into this Library
This repository contains python classes that help working with the Xilinx ISE design suite. This may be for build automatization, for analyzing files generated by ISE or anything else.

## Tagging Policy
Stable releases are tagged in the form *major*.*minor*.*bugfix*. 

* Whenever a change is not fully backward compatible, the *major* version number is incremented
* Whenever new features are added, the *minor* version number is incremented
* If only bugs are fixed (i.e. no functional changes are applied), the *bugfix* version is incremented

# Dependencies
## Library
The required folder structure looks as given below (folder names must be matched exactly). 

Alternatively the repository [psi\_fpga\_all](https://github.com/paulscherrerinstitute/psi_fpga_all) can be used. This repo contains all FPGA related repositories as submodules in the correct folder structure.
* Python
  * [PsiPyUtils](https://github.com/paulscherrerinstitute/PsiPyUtils) (3.0.0 or higher)
    * Can be installed using PIP instead of placing it at this location in the directory structure
  * [**IseScripting**](https://github.com/paulscherrerinstitute/IseScripting)

## External
* None

# Installation
to install, use the command below

```
pip install <root>\dist\IseScripting-<version>.tar.gz
``` 

Alternatively the package can be used directly as git-submodule (as it was done in the past). This allows for being reverse compatible and do not break projects that depend on using the package as submodule.

# Packaing
To package the project after making changes, update the version number in *setup.py* and run

```
python3 setup.py sdist
```

# Content

## Build Scripts
These scripts help to build ISE/EDK/SDK projects from python scripts. The interaction with ISE/EDK/SDK and all workarounds required are encapsulated in this Python module.

Details can be found [here](Build/README.md)









 
