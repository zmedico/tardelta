
import argparse
import collections
import hashlib
import logging
import os
import shlex
import subprocess
import sys
import tarfile


__version__ = "HEAD"
__project__ = "tardelta"
__author__ = "Zac Medico"
__email__ = "<zmedico@gmail.com>"
__copyright__ = "Copyright 2015 Zac Medico"
__license__ = "Apache-2.0"


TAR_FORMATS = collections.OrderedDict((
    ('gnu', tarfile.GNU_FORMAT),
    ('pax', tarfile.PAX_FORMAT),
    ('ustar', tarfile. USTAR_FORMAT),
))


def delta(base_tarfile, deriv_tarfile, delta_tarfile, scratch_db=None):
    """create a delta tar file from base and derived tar files

    :param base_tarfile: base input tar file
    :type base_tarfile: tarfile.TarFile
    :param deriv_tarfile: derived input tar file
    :type deriv_tarfile: tarfile.TarFile
    :param delta_tarfile: delta output tarball
    :type delta_tarfile: tarfile.TarFile
    :param scratch_db: temporary database for comparisons (dict by default)
    :type scratch_db: collections.abc.MutableMapping
    """

    if scratch_db is None:
        scratch_db = {}

    logging.info("digesting base entries...")
    base_count = 0
    for tarinfo in base_tarfile:
        base_count += 1
        scratch_db[tarinfo.name] = _digest_tarinfo(tarinfo)

    logging.info("number of base entries: {}".format(base_count))
    logging.info("reading derived and writing delta...")
    deriv_count = 0
    delta_count = 0
    for tarinfo in deriv_tarfile:
        deriv_count += 1
        base_digest = scratch_db.get(tarinfo.name)
        if base_digest is not None and base_digest == _digest_tarinfo(tarinfo):
            continue
        delta_count += 1
        fileobj = None
        if tarinfo.isreg():
            fileobj = deriv_tarfile.extractfile(tarinfo)
        delta_tarfile.addfile(tarinfo, fileobj=fileobj)

    logging.info("number of derived entries: {}".format(deriv_count))
    logging.info(
        "number of delta entries: {} ({:.0f}% of derived entries)".format(
        delta_count, 100.0 * delta_count/deriv_count))


def _encode_str(s):
    return s.encode(encoding='utf_8', errors='backslashreplace')


_DIGEST_ENCODERS = {
    bytes: lambda b: b,
    int: lambda i: i.to_bytes((i.bit_length() + 7) // 8, 'big') or b'\0',
    str: _encode_str,
}


def _digest_tarinfo(tarinfo):
    """Compute a digest from a tarinfo object.

    :param tarinfo: a tarfile.TarInfo instance
    :type tarinfo: tarfile.TarInfo
    :returns: tarinfo digest
    :rtype: bytes
    """

    m = hashlib.md5()
    for d in (tarinfo.get_info(), tarinfo.pax_headers):
        for k in sorted(d):
            m.update(_encode_str(k))
            v = d[k]
            try:
                encoder = _DIGEST_ENCODERS[v.__class__]
            except KeyError:
                pass
            else:
                m.update(encoder(v))

    return m.digest()


def main():

    formats = list(TAR_FORMATS)
    formats[-1] = 'or {}'.format(formats[-1])
    formats = ', '.join(formats)

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="  {} {}\n{}".format(__project__, __version__,
        "  Generate a tarball of differences between two tarballs"))

    parser.add_argument(
        'base_tarfile',
        action='store',
        metavar="BASE",
        help="base input tar file",
    )
    parser.add_argument(
        'deriv_tarfile',
        action='store',
        metavar="DERIV",
        help="derived input tar file",
    )
    parser.add_argument(
        'delta_tarfile',
        action='store',
        metavar="DELTA",
        help="delta output tar file",
    )
    parser.add_argument(
        '--compressor',
        action='store',
        metavar="COMMAND",
        help="use the specified command for compression via stdio",
    )
    parser.add_argument(
        '--encoding',
        action='store',
        metavar="ENCODING",
        default='UTF-8',
        help="tar file encoding (default is UTF-8)",
    )
    parser.add_argument(
        '--format',
        choices=tuple(TAR_FORMATS),
        metavar="FORMAT",
        default='pax',
        help="tar format: {} (default is pax)".format(formats),
    )
    parser.add_argument(
        '-v', '--verbose',
        dest='verbosity',
        action='count',
        help='verbose logging (each occurence increases verbosity)',
        default=0,
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=(logging.getLogger().getEffectiveLevel() - 10 * args.verbosity),
        format='[%(levelname)-4s] %(message)s',
    )

    tar_format = TAR_FORMATS[args.format]

    compressor_pipe = None
    compressor_proc = None
    output_mode = 'w:{}'.format(args.delta_tarfile[-2:].lower())

    if args.compressor:
        compressor = shlex.split(args.compressor)
        with open(args.delta_tarfile, 'wb') as delta_out:
            compressor_proc = subprocess.Popen(compressor,
                stdin=subprocess.PIPE,
                stdout=delta_out)
        # TarFile will call tell once at the beginning, and it will
        # fail unless it's overridden here.
        compressor_proc.stdin.tell = lambda: 0
        compressor_pipe = compressor_proc.stdin
        output_mode = 'w'

    delta(
        tarfile.open(
            args.base_tarfile,
            format=tar_format,
            encoding=args.encoding,
        ),
        tarfile.open(
            args.deriv_tarfile,
            format=tar_format,
            encoding=args.encoding,
        ),
        tarfile.open(
            args.delta_tarfile,
            mode=output_mode,
            fileobj=compressor_pipe,
            format=tar_format,
            encoding=args.encoding
        ),
    )

    if compressor_proc is not None:
        # Close stdin first, so the compressor reaches EOF and exits.
        compressor_proc.stdin.close()
        if compressor_proc.wait() != os.EX_OK:
            logging.fatal("compressor command failed with return code {}: {}".format(
                compressor_proc.returncode, args.compressor))
            return 1

if __name__ == '__main__':
    sys.exit(main())
