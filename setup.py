from distutils.core import setup 

VERSION = '0.1.0'

setup(
    name='sherilan-easy-conf',
    version=VERSION,
    description='Yet another yaml-based config lib for ML and other stuff.',
    url='https://github.com/sherilan/easy-conf',
    author='sherilan',
    author_email='sherilan@protonmail.com',
    packages=['easy_conf'],
    install_requires=[
      'python_version >= "3.5"',
      'PyYAML',
    ],
)