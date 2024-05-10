import c4d

PLUGIN_INFO = {
    "name": "Omniscient Importer",
    "author": "Stellaxis OÜ",
    "description": "Import data recorded by the Omniscient iOS application.",
    "version": "1.0.1",
    "location": "Extensions > Omniscient Importer"
}

class UnsupportedVersionException(Exception):
    def __init__(self, minimum_required, current_version, update_url=""):
        self.minimum_required = minimum_required
        self.current_version = current_version
        self.update_url = update_url  # Optional: Include a URL for updates
        message = "Update needed: version {0} or higher.|Current version: {1}.".format(self.minimum_required, self.current_version)
        super().__init__(message)


def version_is_greater_or_equal(version_a, version_b):
    """
    Checks if version_a is greater than or equal to version_b.
    
    :param version_a: Version string 'major.minor.patch'.
    :param version_b: Version string to compare to.
    :return: True if version_a >= version_b, False otherwise.
    """
    major_a, minor_a, patch_a = map(int, version_a.split('.'))
    major_b, minor_b, patch_b = map(int, version_b.split('.'))
    return (major_a, minor_a, patch_a) >= (major_b, minor_b, patch_b)

def check_plugin_version(minimum_required_version):
    """
    Compares the current plugin version with the minimum required version.
    
    :param minimum_required_version: The minimum required version string from the .omni file.
    :raises UnsupportedVersionException: If the current version is less than the minimum required version.
    """
    current_version = PLUGIN_INFO["version"]
    update_url = "https://learn.omniscient-app.com/tutorial-thridParty/Cinema4D"
    if not version_is_greater_or_equal(current_version, minimum_required_version):
        raise UnsupportedVersionException(minimum_required_version, current_version, update_url)