from setuptools import setup, find_namespace_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("VERSION", "r") as fh:
    version = fh.read().strip()

setup(
    name='objectref',
    version=version,
    package_dir={'': 'src'},
    packages=find_namespace_packages(include=['cltl.*', 'cltl_service.*'], where='src'),
    package_data={
        "cltl_service.monitoring": ["static/*"]
    },
    data_files=[('VERSION', ['VERSION'])],
    url="https://github.com/leolani/cltl-leolani",
    license='MIT License',
    author='CLTL',
    author_email='t.baier@vu.nl',
    description='Temporary Leolani component',
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires='>=3.7',
    install_requires=["cltl.object-recognition"],
    extras_require={
        "impl": [
            "mock",
            "requests",
            "parameterized"
        ],
        "service": [
            "cltl.combot",
            "cltl.emissordata",
            "cltl.object-recognition",
            "emissor",
        ]
    }
)