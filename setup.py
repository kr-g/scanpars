from setuputil import setuptools, setup_settings, check_setup

setup_settings = setup_settings()

check_setup(setup_settings, prelude=True)

setuptools.setup(**setup_settings)

print("build version tag", setup_settings["version"])

rc = check_setup(setup_settings, prelude=False)

# python3 -m setup sdist build bdist_wheel

# test.pypi
# twine upload --repository testpypi dist/*
# python3 -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ **proj**

# pypi
# twine upload dist/*
