#!python
from setuptools import setup, find_packages

classifiers = ""
version = '0.1.0'

setup(
    name='polar2grid.modis',
    version=version,
    description="Library and scripts to aggregate MODIS data and get associated metadata",
    classifiers=filter(None, classifiers.split("\n")),
    keywords='',
    author='Eva Schiffer, SSEC',
    author_email='eva.schiffer@ssec.wisc.edu',
    url='',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=["polar2grid"],
    include_package_data=True,
    zip_safe=True,
    install_requires=['numpy', 'matplotlib', 'pyhdf', 'polar2grid.core'],
    dependency_links = ['http://larch.ssec.wisc.edu/cgi-bin/repos.cgi'],
    entry_points = {'console_scripts' : [ ]}
)

