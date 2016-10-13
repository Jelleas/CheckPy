from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
	long_description = f.read()

setup(
	name='checkPy',

	version='0.2.7',

	description='A simple python testing framework for educational purposes',
	long_description=long_description,

	url='https://github.com/Jelleas/CheckPy',

	author='Jelleas',
	author_email='jelle.van.assema@gmail.com',

	license='MIT',

	# See https://pypi.python.org/pypi?%3Aaction=list_classifiers
	classifiers=[
		'Development Status :: 3 - Alpha',

		'Intended Audience :: Education',
		'Topic :: Education :: Testing',

		'License :: OSI Approved :: MIT License',

		'Programming Language :: Python :: 2',
		'Programming Language :: Python :: 2.7',
	],

	keywords='new unexperienced programmers automatic testing minor programming',

	packages=find_packages(exclude=[]),

	include_package_data=True,

	install_requires=["requests"],

	extras_require={
		'dev': [],
		'test': [],
	},

	package_data={
	},

	data_files=[],

	entry_points={
		'console_scripts': [
			'checkpy=checkpy.__main__:main',
		],
	},
)
