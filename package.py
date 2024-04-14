import os
import shutil
import zipfile
import re

# Define the name of the plugin folder
plugin_name = "OmniscientImporter"

# Define the root directory of the plugin
plugin_dir = os.path.join(os.getcwd(), plugin_name)
lib_dir = os.path.join(plugin_dir, "lib")

# Define the output folder
output_folder = os.path.join(os.getcwd(), "output")
os.makedirs(output_folder, exist_ok=True)

# Parse version number from PLUGIN_INFO
plugin_info_path = os.path.join(lib_dir, "plugin_version.py")
with open(plugin_info_path, "r") as f:
    plugin_info = f.read()
version_regex = r'"version"\s*:\s*"(\d+)\.(\d+)\.(\d+)"'
version_match = re.search(version_regex, plugin_info)
if version_match:
    version_str = f"v{version_match.group(1)}.{version_match.group(2)}.{version_match.group(3)}"
else:
    version_str = ""

# Define the name of the zip file to create
zip_name = f"{plugin_name}_c4d_{version_str}.zip"

# Define the path to the output zip file
output_zip_path = os.path.join(output_folder, zip_name)

# Remove all __pycache__ folders
for root, dirs, files in os.walk(plugin_dir):
    for dir_name in dirs:
        if dir_name == "__pycache__":
            dir_path = os.path.join(root, dir_name)
            shutil.rmtree(dir_path)

# Remove Mac related files
for root, dirs, files in os.walk(plugin_dir):
    for file_name in files:
        if file_name.startswith(".DS_Store"):
            file_path = os.path.join(root, file_name)
            os.remove(file_path)

# Create the zip file
with zipfile.ZipFile(output_zip_path, "w") as zip_file:
    for root, dirs, files in os.walk(plugin_dir):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            zip_file.write(file_path, os.path.relpath(file_path, plugin_dir))

print(f"Plugin packaged into {output_zip_path}")
