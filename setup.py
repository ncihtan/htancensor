"""genie package setup"""
from importlib.metadata import entry_points
import os
from setuptools import setup, find_packages
import shutil

# figure out the version
about = {}
here = os.path.abspath(os.path.dirname(__file__))
# with open(os.path.join(here, "synapsegenie", "__version__.py")) as f:
#     exec(f.read(), about)

# Add readme
with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='htan-censor',
      # version=about["__version__"],
      description='Tool for de-identifying images submited to HTAN',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://github.com/ncihtan/htancensor',
      author='Adam Taylor',
      author_email='adam.taylor@sagebase.org',
      license='Apache2',
      packages=find_packages(),
      zip_safe=False,
      python_requires='>=3.6',
      install_requires=['tifftools', 'synapseclient'],
      entry_points={
          'console_scripts': ['htancensor=htancensor.censor:main', 'htancensor-synapse=htancensor.synapsecensor:main']
          
      }
)
