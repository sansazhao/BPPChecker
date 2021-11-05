from setuptools import setup, find_packages  
  
setup(  
    name = "BPPChecker",  
    version = "1.0",  
    packages = find_packages(),
    author = 'Jinhao Tan',
    author_email = 'jinhao@sjtu.edu.cn',
    long_description=open('README.md').read(),
    license = 'MIT',
    install_requires = [
        'z3-solver==4.8.5.0'
    ],
    python_requires = '>=3.5',
    entry_points = {
        'console_scripts': [
            'bpptools = bpptools.__main__:main'
        ]
    }
)  
