#!python
from setuptools import setup, find_packages

classifiers = ""
version = '0.0.4a'

setup(
    name='polar2grid',
    version=version,
    description="Library and scripts to remap imager data to a grid",
    classifiers=filter(None, classifiers.split("\n")),
    keywords='',
    author='David Hoese, SSEC',
    author_email='david.hoese@ssec.wisc.edu',
    url='',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=[],
    include_package_data=True,
    package_data={'polar2grid': ["grids/*.gpd","grids/*.nc","*.conf"]},
    zip_safe=False,
    install_requires=['numpy', 'netCDF4', 'matplotlib', 'h5py'],
    dependency_links = ['http://larch.ssec.wisc.edu/cgi-bin/repos.cgi'],
    entry_points = {'console_scripts' : [
            'viirs2awips = polar2grid.viirs2awips:main',
            ]}
)

