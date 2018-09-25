from setuptools import setup, find_packages

MAJOR = 1
MINOR = 0
PATCH = 0
VERSION = "{}.{}.{}".format(MAJOR, MINOR, PATCH)

name = 'florawan_testing'
description = "F-LoRa LoRaWAN testing user Agent."


CLASSIFIERS = [
    "Development Status :: 1 - Betha",
    "Intended Audience :: Science/Research",
    "Intended Audience :: Developers",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Topic :: Internet",
    "Topic :: Software Development :: Testing",
    "Topic :: Scientific/Engineering",
    "Operating System :: POSIX",
    "Operating System :: Unix",
    "Operating System :: MacOS"
]

with open("version.py", "w") as f:
    f.write("__version__ = '{}'\n".format(VERSION))

with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(name=name,
      author="Pablo Modernell",
      author_email="pablomodernell@gmail.com",
      mantainer="Pablo Modernell",
      mantainer_email="pablomodernell@gmail.com",
      description=description,
      long_description=long_description,
      long_description_content_type='text/markdown',
      version=VERSION,
      packages=find_packages(),
      py_modules=['utils', 'message_queueing'],
      include_package_data=True,
      install_requires=[
          'click==6.7',
          'pika==0.12.0',
          'pycryptodomex==3.6.6'
      ],
      entry_points={
          'console_scripts': [
              'flora_start_bridge = lorawan.flora_agent.bridge.bridge_main:agent_main',
              'flora_sniffer = lorawan.flora_agent.packet_sniffer.sniffer_main:sniff',
              'flora_log_tas = lorawan.flora_agent.logger.log_main:log_test_session_coordinator',
              'flora_log_all = lorawan.flora_agent.logger.log_main:log_all',
          ]
      },
      )
