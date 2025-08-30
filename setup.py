from setuptools import setup

setup(
    name='pyrest',
    version='0.1',
    py_modules=['main', 'rest_client'],
    install_requires=[
        'requests',
        'prompt_toolkit',
    ],
    entry_points={
        'console_scripts': [
            'pyrest=main:main',  # If your main entry is main.py and main() is the entry function
        ],
    },
)