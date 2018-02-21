Debugging guide
================

Debugging with PyDev
------------------------
 
These instructions explain how to connect the PyDev debugger to the code running in the containers:
 
  1. Install Eclipse and PyDev
  
  2. Create a new project:
  
     1. "File" -> "New" -> "Project..."
     2. Select "PyDev Project"
     3. Fill the form:
       - Select 3.0-3.5 in "Grammar version"
       - Select "Create links to existing sources"
     4. Press "Next >"
     5. Click on "Add External source folder..." and add the root of the pipeline project and press "Next >"
     6. Do not add any related project
     
  3. Start the debugger server:
  
     1. Click on "Window" -> "Perspective" -> "Open Perspective" -> "Other..." and select "Debug"
     2. Click on the menu "PyDev" -> "Start Debug Server"
     3. Note down the port on which the server is running (this is written in the console window)
  
  4. Modify the Dockerfile of the container you want to debug:
  
     1. Add the command "RUN pip3 install pydevd" before the CMD command
     2. Add the following lines where you want to start to debug:

        import pydevd
        pydevd.settrace('192.168.1.1', port=5678, stdoutToServer=True, stderrToServer=True)
     
        where '192.168.1.1' is the IP address of the machine with the debugger and 5678 is the port where the debugger
        is listening.
        
        Notice that the containers have two python processes: one that runs the webserver and one that does the artifact
        creation. You need to add the lines above to the code executing in the appropriate process.

After this setup you can start the pipeline as usual. When the pydevd code is execute you will see a new process in 
eclipse and you can start debugging the process.