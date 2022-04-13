# Experimental HTTP/2 plugin for HTTPie through HTTPX

This is a **highly experimental** plugin for [HTTPie](https://github.com/httpie/httpie)
that adds HTTP/2 support. It is based on the original work by [Tom Christie](https://github.com/tomchristie) on a [PR against HTTPie's core](https://github.com/httpie/httpie/pull/972). Instead of embedding this directly, this is a plugin for experimenting on the idea of what sort of changes do we need to make in the core in order to support different Python backends (`requests`, `httpx`, etc).
