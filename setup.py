from setuptools import setup

setup(
    name="httpie-httpx",
    version="0.0.1",
    description=(
        "httpie-httpx is a plugin for HTTPie that uses httpx under the hood"
        " for HTTP/2."
    ),
    py_modules=["httpie_httpx"],
    entry_points={
        "httpie.plugins.transport.v1": [
            "httpx = httpie_httpx:HTTPXTransport",
        ],
    },
    install_requires=["httpcore[http2]==0.14.7", "httpx==0.22.0"],
)
