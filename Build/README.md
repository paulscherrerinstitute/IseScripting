# Known Issues

## Incorrect Path for ELF-Check
SDK by defaults sets the path to the HW specification used for the ELF-check in a way that only works when used from the eclipse GUI. When the project is compiled from the command-line (which the scripts do), the ELF-Check fails and SDK hangs (i.e. the scripts will not respond).

To avoid this behavior, the path to the HW specification for the ELF-check must be given relative to the project directory (eclipse variable *$(ProjDirPath)*) for all build configurations (usually *Debug* and *Release*) because the scripts always build all configurations.

This can be done in the GUI (for all Configurations!):
AppProject > Properties > C/C++ Build > Settings > Tool Settings > Xilinx ELF Check > Options > Hardware Specification
Example: -hw ${ProjDirPath}/../hw/system.xml

It is also possible to change the path directly in the *.cproject* file. The corresponding entries can easily be found by searching for *elfcheck*.

# Build Script Usage

## Build a EDK Project
```
#Configure
#  ISE_14_7: Environment variable pointing to the ISE installation (e.g. C:\Xilinx\14.7)
#  14.7:     String for the version. This is required to handle differences between vivado versions
edk = Edk("ISE_14_7", "14.7")

#Build project
edk.CleanBuild("../system.xmp", "build.log")

#Export HW to sdk (in this case into ../sw/hw)
edk.ExportHw("../system.xmp", "../sw", "export.log")
```


## Build an SDK Project
```
#Configure
#  ISE_14_7: Environment variable pointing to the ISE installation (e.g. C:\Xilinx\14.7)
#  14.7:     String for the version. This is required to handle differences between vivado versions
sdk = Sdk("ISE_14_7", "14.7")

#Create workspace and import projects
sdk.CreateNewWs("../sw/hw", "../sw/bsp", "../sw/sw", "./ws")
                           
#Create BSP and build
sdk.GenerateBspForCreatedWs("microblaze_inst")
sdk.BuildCreatedWs()

#Update bitstream with the SW binary
sdk.CreateBitstreamWithSw("../sw/hw/system_bd.bmm", "../sw/hw/system.bit",
                          "../sw/sw/Debug/sw_cfg_gpac21.elf", "../sw/hw/download.bit")
```

## Build an ISE Project
```
#Configure
#  ISE_14_7: Environment variable pointing to the ISE installation (e.g. C:\Xilinx\14.7)
#  14.7:     String for the version. This is required to handle differences between vivado versions
ise = Ise("ISE_14_7", "14.7")

#Build Project
ise.BuildProject("adc16hl_fpga.xise", "build.log")

#Check timing score
if ise.TimingScore != 0:
    raise Exception("Timing Score not Zero")
```

## Create a Flash Image from Multiple Bitstreams
```
#Configure
#  ISE_14_7: Environment variable pointing to the ISE installation (e.g. C:\Xilinx\14.7)
#  14.7:     String for the version. This is required to handle differences between vivado versions
tools = Tools("ISE_14_7", "14.7")

#Configure address mapping of the bitstreams
bitstreams = {"0x00000000" : "./path/to/bitstreamA.bit",
              "0x01400000" : "./path/to/bitstreamB.bit"}
tools.Promgen("../sw/hw/generated.mcs", bitstreams=bitstreams, device="xcf04s", fmt="mcs")
```


## Use Impact
```
#Configure
#  ISE_14_7: Environment variable pointing to the ISE installation (e.g. C:\Xilinx\14.7)
#  14.7:     String for the version. This is required to handle differences between vivado versions
impact = Impact("ISE_14_7", "14.7")

# Run Impact in batch mode
impact.ExecBatch("gen_ace.cmd")



