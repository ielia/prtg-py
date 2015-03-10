from setuptools import setup

setup(
    name='prtg-py',
    version='0.0.1',
    description='A Python client for PRTG',
    url='http://github.com/ielia/prtg-py',
    author='Kevin Schoon',
    author_email='kevinschoon@gmail.com',
    maintainer='Ignacio Elia',
    maintainer_email='ielia@olenick.com',
    keywords=['PRTG', 'Network Monitoring'],
    license='MIT',
    packages=['prtg'],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='tests'
)
