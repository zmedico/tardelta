# tardelta

Generate a tarball of differences between two tarballs.

## Motivation
It is possible to optimize docker containers such that multiple containers
are based off of a single copy of a common base image. If containers are
constructed from tarballs, then it can be useful to create a delta tarball
which contains the differences between a base image and a derived image. The
delta tarball can then be layered on top of the base image using a Dockerfile
like the following:
```
FROM base
ADD delta.tar.xz
```
Many different types of containers can thus be derived from a common base
image, while sharing a single copy of the base image. This saves disk space,
and can also reduce memory consumption since it avoids having duplicate
copies of base image data in the kernel's buffer cache.

## Usage
```
usage: tardelta [-h] [--compressor COMMAND] [--encoding ENCODING]
                [--format FORMAT] [-v]
                BASE DERIV DELTA

  tardelta
  Generate a tarball of differences between two tarballs

positional arguments:
  BASE                  base input tar file
  DERIV                 derived input tar file
  DELTA                 delta output tar file

optional arguments:
  -h, --help            show this help message and exit
  --compressor COMMAND  use the specified command for compression via stdio
  --encoding ENCODING   tar file encoding (default is UTF-8)
  --format FORMAT       tar format: gnu, pax, or ustar (default is pax)
  -v, --verbose         verbose logging (each occurence increases verbosity)
```
