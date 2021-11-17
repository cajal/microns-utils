"""
Methods for checking installed and latest versions of microns packages.
"""

import traceback
import requests
from importlib import metadata
import warnings
import re
import os
import sys
import json


def find_all_matching_files(name, path):
    """
    Finds all files matching filename within path.

    :param name (str): file name to search
    :param path (str): path to search within
    :returns (list): returns list of matching paths to filenames or empty list if no matches found. 
    """
    result = []
    for root, _, files in os.walk(path):
        if name in files:
            result.append(os.path.join(root, name))
    return result


def parse_version(text: str):
    """
    Parses the text from version.py, where version.py contains one variable:
    
    __version__ = "x.y.z", where "x.y.z" must follow semantic versioning (https://semver.org/).
    
    Function is also compatible with a direct version input, i.e.: "x.y.z". 
    
    :param text (str): the text from the version.py file.
    :returns (str): version if parsed successfully else ""
    """
    semver = "^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
    text = text.strip('\n')
    text = text.split('=')[1].strip(' "'" '") if len(text.split('='))>1 else text.strip(' "'" '")
    parsed = re.search(semver, text)
    return parsed.group() if parsed else ""


def get_latest_version_from_github(repo, owner, branch, source, path_to_version_file=None, warn=True):
    """
    Checks github for the latest version of package.

    :param repo (str): name of repository that contains package
    :param user (str): owner of repository
    :param branch (str): branch of repository (if source='commit')
    :param tag (str): specifed tag  (if source='tag')
    :param source (str): 
        options: 
            "commit" - gets version of latest commit
            "tag" - gets version of latest tag
            "release" - gets version of latest release
    :param path_to_version_file (str): path to version.py file from top of repo if source = "commit". 
    :param warn (bool): warnings enabled if True
    :returns (str): returns latest version according to source if found, else ""
    """
    latest = ""
    try:
        if source == 'commit':
            assert path_to_version_file is not None, 'Provide path_to_version_file if source = "commit".'
            f = requests.get(f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path_to_version_file}")
            latest = parse_version(f.text)
            
        elif source == 'tag':
            f = requests.get(f"https://api.github.com/repos/{owner}/{repo}/tags")
            latest = parse_version(json.loads(f.text)[0]['name'][1:])
            
        elif source == 'release':
            f = requests.get(f"https://api.github.com/repos/{owner}/{repo}/releases")
            latest = parse_version(json.loads(f.text)[0]['tag_name'][1:])
        else:
            raise ValueError(f'source: "{source}" not recognized. Options include: "commit", "tag", "release". ')
    except:
        if warn:
            warnings.warn('Failed to reach Github during check for latest version.')
            traceback.print_exc()

    return latest


def get_package_version_from_distributions(package, warn=True):
    """
    Checks importlib metadata for an installed version of the package. 
    Note: packages installed as editable (i.e. pip install -e) will not be found.

    :param package (str): name of package:
    :returns (str): package version
    """
    version = [dist.version for dist in metadata.distributions() if dist.metadata["Name"] == package]
    if not version:
        if warn:
            warnings.warn('Package not found in distributions.')
        return ''
    return version[0]


def get_package_version_from_sys_path(package, path_to_version_file, warn=True):
    """
    Checks sys.path for package and returns version from internal version.py file.
    
    :param package (str): name of package. must match at the end of the path string in sys.path.
    :param path_to_version_file (str): path to version.py file relative to package path in sys.path.
    :param warn (bool): warnings enabled if True
    :return (str): package version
    """
    path = ''.join([p + path_to_version_file for p in sys.path if re.findall(package+'$', p)])
    file = find_all_matching_files('version.py', path)

    if len(file) == 0:
        if warn:
            warnings.warn('No version.py file found.')
        return ''

    elif len(file) > 1: 
        if warn:
            warnings.warn('Multiple version.py files found.')
        return ''

    else:
        with open(file[0]) as f:
            lines = f.readlines()[0]
        
    return parse_version(lines)


def get_package_version(package, check_if_latest=False, check_if_latest_kwargs={}, warn=True):
    """
    Gets package version.

    :param package (str): name of package (contains setup.py)
    :param check_if_latest (bool): if True, checks if installed version matches latest version on Github 
    :check_if_latest_kwargs (dict): kwargs to pass to "get_latest_version_from_github". 
    :param warn (bool): warnings enabled if True
    :returns (str): current package version
    """
    # check installed distributions for versions
    dist_version = get_package_version_from_distributions(package=package, warn=False)

    if not dist_version:
        # check sys.path for versions
        sys_version = get_package_version_from_sys_path(package=package, path_to_version_file='/..', warn=warn)
        if not sys_version:
            return ''
        else: 
            __version__ = sys_version
    else:
        __version__ = dist_version

    if check_if_latest:
        # check if package version is latest
        latest = get_latest_version_from_github(**check_if_latest_kwargs)

        if __version__ != latest:
            if warn:
                warnings.warn(f'You are using {package} version {__version__}, which is not the latest version. Version {latest} is available. Upgrade to avoid conflicts with the database.')
    
    return __version__