@echo off

::
:: Publish the package to PyPi and clean up afterwards.
::

python setup.py bdist_wheel 
twine upload dist/* 
rm -rf ./build ./dist ./*egg-info