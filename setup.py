#
# A Python client API for Edbot Studio with vendor specific utils.
#
# Copyright (c) Robots in Schools Ltd. All rights reserved.
#

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
	long_description = fh.read()

setuptools.setup(
	name = "edbotstudio",
	version = "1.0.1",
	description = "A Python client API for Edbot Studio",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url = "https://github.com/edbotstudio/client-python",
	project_urls = {
		"Bug Tracker": "https://github.com/edbotstudio/client-python/issues"
	},
	author = "Clive Haworth",
	author_email = "clive@ed.bot",
	license = "MIT",
	packages = [ "edbotstudio" ],
	package_dir = { "edbotstudio": "src" },
	install_requires = [ "ws4py", "pydash" ],
	python_requires= ">=3",
	classifiers = [
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent"
	]
)