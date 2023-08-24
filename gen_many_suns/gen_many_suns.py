# -*- coding: utf-8 -*-
"""
Python code to generate a Radiance sun description of many suns, based on a 
Radiance sun description of one sun.
The scripts only works on Windows.
Make sure Radiance is installed and the script is in the same folder as the template files.
To run the code supply the name of the original (single) sun description and 
the dimension (in pixels) of the side of a square on which the sun should be based.
A solar angular opening of 0.533 degrees is assumed.

This program has been developed by Sietse de Vries in the context of IntelLight+, an Eindhoven Engine project (partners: Signify, Eindhoven University of Technology).
The program is licensed under the BSD-3 license, see the LICENSE file.

"""

import subprocess
import shutil
import math
import os
import re
import sys
from pathlib import Path


def check_templates(file_path: Path) -> None:
    """
    This function checks if the needed templates are available.
    
    Args:
        file_path : The path to the folder containing the script, template files 
        and the orginal sun description file. 
        
    Returns:
        None
    """
    sun_template = file_path / "001-sun_template.rad"
    vf_template = file_path / "x.vf"
    NNN_sun_template = file_path / "NNN-sun_template.rad"
    manysun_template = file_path / "manysun.fmt"
    missing_files = []
    
    print(f"Looking for template files in {file_path}")
    for file in [sun_template, vf_template, NNN_sun_template, manysun_template]:
        if not os.path.exists(file):
            missing_files.append(file)

    if missing_files:
        raise FileNotFoundError("The following templates are missing:", missing_files)

    print("All templates found.")
    

def execute_gendaylit_gensky(file_path: Path, sun_description: str) -> None:
    """
    This function checks if the supplied sun description has !Gendaylit or 
    !Gensky written at the top. It needs to be executed so the output can be 
    read.
    
    Args:
        file_path : The path to the folder containing the script, template files 
        and the orginal sun description file. 
        sun_description : The name of the sun description file
        
    Returns:
        Changes are made to the supplied sun description file
    """    
    
    with open(file_path / sun_description, 'r') as file:
        lines = file.readlines()

    for i, line in enumerate(lines):
        if '!gendaylit' in line or '!gensky' in line:
            modified_line = line.replace('!', '')
            results = subprocess.check_output(modified_line, shell=True).decode('UTF-8').replace('\n', '')

            lines[i] = results.strip()
            print('Executed Gendaylit or Gensky to prepare sun description for conversion')
            break

    with open(file_path / sun_description, 'w') as file:
        file.writelines(lines)


def check_sun_description(file_path: Path, sun_description: str) -> None:
    """
    This function checks if the supplied sun description has 'void light solar' 
    and 'solar source sun' defined. Additionally, it removes any unnecessary 
    tabs or spaces.
    
    Args:
        file_path : The path to the folder containing the script, template files 
        and the orginal sun description file. 
        sun_description : The name of the sun description file
        
    Returns:
        Changes are made to the supplied sun description file
    """
    pattern1 = r'\bvoid\s+\s*light\s+\s*solar\b'
    pattern2 = r'\bsolar\s+\s*source\s+\s*sun\b'
    has_void_light_solar = False
    has_solar_source_sun = False
    modified_lines = []

    with open(file_path / sun_description, 'r') as file:
        for line in file:
            if re.search(pattern1, line):
                has_void_light_solar = True
                line = re.sub(r'\s+', ' ', line)

            if re.search(pattern2, line):
                has_solar_source_sun = True
                line = re.sub(r'\s+', ' ', line)

            modified_lines.append(line.strip())

    with open(file_path / sun_description, 'w') as file:
        file.write('\n'.join(modified_lines))

    if has_void_light_solar and has_solar_source_sun:
        print("Sun description ready for conversion")
    else:
        error_message = "Sun description is incomplete. "
        if not has_void_light_solar:
            error_message += "Void light solar not found. "
        if not has_solar_source_sun:
            error_message += "Solar source sun not found. "
        raise ValueError(error_message + "Please define void light solar and/or solar source sun.")


def find_sun_properties(file_path: Path, sun_description: str) -> None:
    """
    This function extracts the sun Radiance (RGB) and sun direction vector 
    (XYZ) of the supplied sun description.
    Based on the sun direction vector the corresponding solar altitude and 
    aziumth are calculated.
    
    Args:
        file_path : The path to the folder containing the script, template files 
        and the orginal sun description file. 
        sun_description : The name of the sun description file
        
    Returns:
        RGB_sun_radiance : The sun RGB Radiance in the supplied sun description 
        file
        XYZ_sun_direction : The sun direction vector in the supplied sun 
        description file
        altitude : The altitude of the supplied sun description file
        azimuth : The azimtuth of the supplied sun description file
    """
    # Extract sun Radiance (RGB)
    with open(file_path / sun_description, 'r') as file:
        lines = file.readlines()

    result_lines = []
    count = 0

    for line in lines:
        if line.startswith('void light solar') and count < 4:
            result_lines.append(line)
            count += 1
        elif count > 0 and count < 4 and line.strip() != '':
            result_lines.append(line)
            count += 1
        
    if result_lines:
        last_line_values = result_lines[-1].split()[1:]
        RGB_sun_radiance = last_line_values[-3:]
        
        print(f"Sun Radiance of the supplied sun description (RGB) found at: {RGB_sun_radiance}")    


    # Extract sun direction vector (XYZ)
    result_lines = []
    count = 0

    for line in lines:
        if line.startswith('solar source sun') and count < 4:
            result_lines.append(line)
            count += 1
        elif count > 0 and count < 4 and line.strip() != '':
            result_lines.append(line)
            count += 1
            
    if len(result_lines) > 0:
        last_line_values = result_lines[-1].split()[1:]
        XYZ_sun_direction = last_line_values[:3]
        XYZ_sun_direction = [float(coord) for coord in XYZ_sun_direction]
        print(f"Sun direction vector (XYZ) of the supplied sun description found at: {XYZ_sun_direction}")
        
    # Calculate the solar altitude and azimuth
    altitude = math.degrees(math.asin(XYZ_sun_direction[2]))
    print(f"Calculated solar altitude of the supplied sun description at {altitude}")

    xDIVcos_altitude = XYZ_sun_direction[0] / (math.cos(math.radians(altitude)))

    # Values higher than 1 are rounded to 1 to prevent a math error
    if xDIVcos_altitude > 1:
        xDIVcos_altitude = 1

    azimuth_x = -math.degrees(math.asin(xDIVcos_altitude))    

    if XYZ_sun_direction[0] < 0 and XYZ_sun_direction[1] < 0:
        azimuth = azimuth_x
    elif XYZ_sun_direction[1] >= 0:
        azimuth = 180 - azimuth_x
    elif XYZ_sun_direction[0] >= 0 and XYZ_sun_direction[1] < 0:
        azimuth = 360 + azimuth_x

    print(f"Calculated solar azimuth of the supplied sun description at {azimuth}")    
    
    return RGB_sun_radiance, XYZ_sun_direction, altitude, azimuth


def set_irradiance(file_path, RGB_original_radiance):
    """
    This function copies the 001-sun_template.rad file to a file called 
    001_sun.rad. 
    In the new file, the Radiance (RGB) is set equal to the Radiance of the 
    supplied sun description.
    
    Args:
        file_path : The path to the folder containing the script, template files 
        and the orginal sun description file
        RGB_original_radiance : The sun RGB Radiance in the supplied sun 
        description file
    
    Returns:
        Changes are made in 001-sun.rad
    """
    shutil.copyfile(file_path / "001-sun_template.rad", file_path / "001-sun.rad")

    with open(file_path / "001-sun.rad", 'r') as file:
        lines = file.readlines()
    modified_lines = [line.replace("RADR", RGB_original_radiance[0]).replace("RADG", RGB_original_radiance[1]).replace("RADB", RGB_original_radiance[2]) for line in lines]

    with open(file_path / "001-sun.rad", 'w') as file:
        file.writelines(modified_lines)
    print(f"Created standard sun 001-sun.rad with RGB Radiance {RGB_original_radiance} (equal to the supplied sun description)")


def gensunvecs(file_path: Path, pdim: int) -> int:
    """
    Generates a list of sun vectors based on the number of pixels in a circle 
    inscribed in the supplied square area. 
    
    Args:
        file_path : The path to the folder containing the script, template files 
        and the orginal sun description file.  
        pdim : The length (in pixels) of one side of the square area to be used 
        for generating the suns
    Returns:
        Changes are made in 001-sun.rad
        count : The number of direction vectors (mini-suns) generated
    """

    res = f"-x {pdim} -y {pdim}"
    hdr = file_path / f"{pdim}-sun.hdr"
    
    # render an image of the standard sun
    os.system(f"oconv {file_path}/001-sun.rad > {file_path}/001-sun.oct")
    os.system(f"rpict -vf {file_path}/x.vf {res} -pj 0 -ps 1 -w {file_path}/001-sun.oct > {hdr}")	

    sunvec = f"{pdim}-sun.vec"
    # Generate a list of vectors based on a render of the standard sun
    os.system(f"rlam  \"!vwrays {hdr} | rtrace -h -w -od {file_path}/001-sun.oct\"  \"!pvalue -h -H -d -b  \"{hdr} | rcalc  -e \"$1=$1;$2=$2;$3=$3;cond=$4-1\" > {file_path}/{sunvec}")
            
    with open(file_path / f"{sunvec}", 'r') as file:
        count = sum(1 for _ in file)
    print(f"Direction vectors for {count} mini suns, based on an image of {pdim}x{pdim} pixels written to file: {pdim}-sun.vec")
    return count


def gensunrad(file_path: Path, sun_description: str, pdim: int, count: int, altitude, azimuth) -> None:
    """
    Creates a rad file (NNN-sun.rad) of a sun consisting of NNN mini suns, 
    based on the NNN-sun_template file.
    Calculates the irradiance of 001-sun.rad, and calculates the irradiance of 
    NNN-sun.rad.
    Increases the Radiance of NNN-sun.rad to achieve equal irradiance.
    Changes the location of NNN-sun.rad (through Radiance Xform) to set the 
    location equal to the altitude
    and azimuth of the supplied sun description.
    
    Args:
        sun_description : The name of the sun description file
        file_path : The path to the folder containing the script, template files 
        and the orginal sun description file. 
        pdim : The length (in pixels) of one side of the square area to be 
        used for generating the suns
        count : The number of mini suns generated
        altitude : The altitude to set the many suns at
        azimuth : The azimtuth to set the many suns at
    Returns:
        A rad file is created that has a large number of mini suns with equal 
        irradiance and location as the supplied sun description.
    """
    
    # Check if the need list of sun vectors was created
    sunvec = f"{pdim}-sun.vec"
    if os.path.isfile(file_path / f"{sunvec}"):
        pass
    else:
        error_message = f"{sunvec} cannot be found. Has the file been generated?"
        raise FileNotFoundError(error_message)

    # Create NNN-sun.rad file and link to NNN-vec
    shutil.copyfile(file_path / "NNN-sun_template.rad", file_path / f"{pdim}-sun.rad")

    with open(file_path / f"{pdim}-sun.rad", "r") as file:
        content = file.read().replace("NNN", f"{pdim}")
    with open(file_path / f"{pdim}-sun.rad", "w") as file:
        file.write(content)
    print(f"Used {sunvec} and NNN-sun_template.rad to create descriptions of {count} suns: {pdim}-sun.rad")

    # Calculate (direct normal) irradiance for a surface orientated in the +ve x direction
    # Standard sun (001)
    os.system(f"oconv {file_path}/001-sun.rad > {file_path}/001-sun.oct")
    irrad_001 = float(subprocess.check_output(f"echo 0 0 0 1 0 0 | rtrace -w -h -I -dc 1 -dt 0 {file_path}/001-sun.oct | rcalc -e \"$1=($1*0.265+$2*0.670+$3*0.065)\"", shell=True).decode('UTF-8'))
    print(f"Irradiance of standard sun (001-sun.rad) calculated at: {irrad_001} W⋅m²")

    # Many suns (NNN)
    os.system(f"cd {file_path} & oconv -f {file_path}/{pdim}-sun.rad > {file_path}/{pdim}-sun.oct")
    irrad_NNN = float(subprocess.check_output(f"cd {file_path} & echo 0 0 0 1 0 0 | rtrace -w -h -I -dc 1 -dt 0 {file_path}/{pdim}-sun.oct | rcalc -e \"$1=($1*0.265+$2*0.670+$3*0.065)\"", shell=True).decode('UTF-8'))
    print(f"Irradiance of {count} suns ({pdim}-sun.rad) calculated at: {irrad_NNN} W⋅m²")

    # Calculate the Radiance of many suns needed to get equal irradiance
    rad_NNN = 10000 * irrad_001 / irrad_NNN # The Radiance in NNN-sun.rad was set arbitrarily at 1E4, hence 10000 in this line.

    with open(file_path / f"{pdim}-sun.rad", "r") as file:
        content = file.read().replace("1E4", f"{rad_NNN}")
    with open(file_path / f"{pdim}-sun.rad", "w") as file:
        file.write(content)
    print(f"Set Radiance in {pdim}-sun.rad at {rad_NNN} to achieve equal irradiance")

    # Change Location of the many suns based on the solar altitude and azimuth
    azimuth_xform = azimuth + 90 # Correct for the standard sun being along the X-axis (1,0,0), while the azimuth is caluclated from the negative Y-axis (0,-1,0)

    # Apply Radiance xform
    os.system(f"cd {file_path} & xform -ry -{altitude} -rz -{azimuth_xform} {file_path}/{pdim}-sun.rad > {file_path}/{pdim}-sun_xform.rad")
    print(f"Changed the sun location to altitude: {altitude}, azimuth:{azimuth} degrees in {pdim}-sun_xform.rad")
   
    # Copy the (original) supplied sun description, and replace the single sun with many suns
    shutil.copyfile(file_path / f"{sun_description}", file_path / f"{sun_description}-{count}-suns.rad")

    with open(file_path / f"{sun_description}-{count}-suns.rad", 'r') as file:
        lines = file.readlines()
    with open(file_path / f"{pdim}-sun_xform.rad", 'r') as file:
        new_lines = file.readlines()    
    
    start_index = lines.index('void light solar\n')
    end_index = lines.index('solar source sun\n') + 4
    lines[start_index:end_index] = new_lines

    with open(file_path / f"{sun_description}-{count}-suns.rad", 'w') as file:
        file.writelines(lines)
   
    print(f"Created {sun_description}-{count}-suns.rad with {count} mini suns")


def main():
    if len(sys.argv) != 3:
        error_message = "Usage: python gen_many_suns.py original_sun_description square_side_length"
        raise ValueError(error_message)

    script_path = os.path.abspath(sys.argv[0])
    original_sun_description = sys.argv[1]
    square_side = int(sys.argv[2])
    script_dir = Path(os.path.dirname(script_path) + os.path.sep)

    # Checks files & prepare for conversion
    check_templates(script_dir)
    execute_gendaylit_gensky(script_dir, original_sun_description)
    check_sun_description(script_dir, original_sun_description)

    # Identify data in supplied sun description
    RGB_original_radiance_found, XYZ_original_direction_found, altitude, azimuth = find_sun_properties(script_dir, original_sun_description)

    # Create new sun description with same irradiance and location
    set_irradiance(script_dir, RGB_original_radiance_found)
    num_suns = gensunvecs(script_dir, square_side)
    gensunrad(script_dir, original_sun_description, square_side, num_suns, altitude, azimuth)


if __name__ == "__main__":
    main()
