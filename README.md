# sot-gepetto-viewer

Viewing tools for Stack of Tasks library.

This document will show the steps to install sot-gepetto-viewer and configure gepetto-gui.

Important : This plugin will only work if an instance of gazebo can work on your computer.

Before doing anything, you will need to install several packages that are needed for the installation process, you will need to install the following packages:
 - sudo apt install robotpkg-qt4-qgv
 - sudo apt install robotpkg-py27-qt4-gepetto-pythonqt		(make sure your version of python is the 2.7)
 - sudo apt-get install libqtwebkit4
 - sudo apt install cmake-curses-gui				(will allow you to use the ccmake command)
 - sudo apt-get install libomniorb4-dev
 - sudo apt-get install libopenscenegraph-dev
 - sudo apt-get  install omniidl-python


Now you will need to get 3 git repository on your computer, you will need to install them as follow.
You will need to install gepetto-viewer, gepetto-viewer-corba and sot-gepetto-viewer.

Installing gepetto-viewer:
 1. clone the repository on your computer : git clone --recursive https://github.com/Gepetto/gepetto-viewer 		(--recursive will allow you to use the cmake command)
 2. create of folder name _build in the folder gepetto-viewer
 3. open a terminal in the new folder
  1. in the terminal, do "cmake .."
  2. do "ccmake .."
   1. make sure to change the variable BUILD_PY_QCUSTOM_PLOT, BUILD_PY_QGV and GEPETTO_GUI_HAS_PYTHONQT to ON
   2. change the CMAKE_INSTALL_PREFIX path to a new folder Install (this path will be important later)
  3. do "make install"

If no problem was encountered, gepetto-viewer is now installed.

Installing gepetto-viewer-corba :
 1. open the file ~/.bashrc and add :
  my_install_dir= "your CMAKE_INSTALL_PREFIX path for gpetto-viewer"
  export PATH=$my_install_dir/bin:$PATH
  export LD_LIBRARY_PATH=$my_install_dir/lib:$LD_LIBRARY_PATH
  export PYTHONPATH=$my_install_dir/lib/python2.7/site-packages:$PYTHONPATH
  export PKG_CONFIG_PATH=$my_install_dir/lib/pkgconfig/:$PKG_CONFIG_PATH
  export ROS_PACKAGE_PATH=$my_install_dir/share:$ROS_PACKAGE_PATH
  export CMAKE_PREFIX_PATH=$my_install_dir:$CMAKE_PREFIX_PATH

You will need to add these lines because corba doesn't automaticly detect gepetto-viewer.
 2. clone the repository on your computer : git clone --recursive https://github.com/Gepetto/gepetto-viewer-corba
 3. create of folder name _build in the folder gepetto-viewer
 4. open a terminal in the new folder
  1. in the terminal, do "cmake .."
  2. do "ccmake .."
   1. change the CMAKE_INSTALL_PREFIX path to the Install folder
  3. make install

gepetto-viewer-corba is now installed.

Important! Make sure the global variable CMAKE_PREFIX_PATH contain the path to pythonqt and qgv, both normal path should be /opt/openrobots

Installing sot-gepetto-viewer:
 1. clone the repository on your computer : git clone --recursive https://github.com/AlexKuen/sot-gepetto-viewer
 2. create of folder name _build in the folder gepetto-viewer
 3. open a terminal in the new folder
  1. in the terminal, do "cmake .."
  2. do "ccmake .."
   1. change the CMAKE_INSTALL_PREFIX path to the Install folder
  3. do "make install"

sot-gepetto-viewer is now installed, the plugin can now be configured.

Confiurate gepetto-gui
 1. Open a terminal and do "gepetto-gui"
 Gepetto-gui will now open.
 2. click on "Plugins", normally you will only see OmniORB Server detected and loaded.
 3. Click on "Find all lugins", PyPCustomPlot and PyQGV will be detected, load them if they are not already loaded (right click then click load)
 4. click on save

gepetto-gui is now configure.

If you want to launch the new plugin, you will need to write "gepetto-gui --load-pyplugin sot_gepetto_viewer.sot_plugin" in the terminal
