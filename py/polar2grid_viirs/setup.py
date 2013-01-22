#!python
from setuptools import setup, find_packages

classifiers = ""
version = '1.0.0'

setup(
    name='polar2grid.viirs',
    version=version,
    description="Library and scripts to aggregate VIIRS data and get associated metadata",
    classifiers=filter(None, classifiers.split("\n")),
    keywords='',
    author='David Hoese, SSEC',
    author_email='david.hoese@ssec.wisc.edu',
    url='',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=["polar2grid"],
    include_package_data=True,
    zip_safe=True,
    install_requires=[
        'numpy',
        'h5py',
        'polar2grid.core'
        ],
    dependency_links = ['http://larch.ssec.wisc.edu/cgi-bin/repos.cgi'],
    entry_points = {'console_scripts' : [ ]}
)

