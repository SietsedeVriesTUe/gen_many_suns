# gen_many_suns
Python code to generate a Radiance sun description of many suns, based on a Radiance sun description of one sun.

# How to use
Save all files in one folder. Open your terminal or command prompt, navigate to the folder, and execute gen_many_suns.py by providing the name of the original (single) sun description file and the desired dimension (in pixels) of the side of the square on which the suns should be based. A dimension of 32 pixels results in 632 suns, which is deemed adequate for most applications.

Example Command:
python gen_many_suns.py original_sun_description.rad 32

More information will be available soon at https://www.radiance-online.org/community/workshops/2023-innsbruck-austria

# Requirements
The script currently only works for windows.
Make sure you have Radiance installed.
Python libraries: subprocess, shutil, math, os, re, sys, path

# License and citation
This program is licensed under the BSD 3-Clause.
Please refer to this program by citing: XX

![Image](manysuns.png) 
