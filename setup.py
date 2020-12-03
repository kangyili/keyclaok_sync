from setuptools import setup

setup(
    name="keycloak_sync",
    version='0.1.0',
    packages=['keycloak_sync'],
    entry_points={
        "console_scripts": [
            'kc = keycloak_sync.kctool:main',
        ]
    },
)
