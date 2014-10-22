#!python
from setuptools import setup, find_packages

classifiers = ""
version = '1.0.0'

setup(
    name='polar2grid.acspo',
    version=version,
    description="Library and scripts to aggregate and extra data processed with the ACSPO software",
    classifiers=filter(None, classifiers.split("\n")),
    keywords='',
    author='David Hoese, SSEC',
    author_email='david.hoese@ssec.wisc.edu',
    url='',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=["polar2grid"],
    include_package_data=True,
    zip_safe=True,
    install_requires=['numpy', 'matplotlib', 'netCDF4', 'polar2grid.core'],
    dependency_links=['http://larch.ssec.wisc.edu/cgi-bin/repos.cgi'],
    entry_points={
        'console_scripts': [],
        'polar2grid.frontend_class': ['acspo=polar2grid.acspo:Frontend'],
        'polar2grid.frontend_arguments': ['acspo=polar2grid.acspo:add_frontend_argument_groups']
    }
)

