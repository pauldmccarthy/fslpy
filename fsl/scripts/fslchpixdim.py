#!/usr/bin/env python
#
# fslchpixdim - change pixel dimensions, but keep everything else the same
#

import                      sys
import numpy             as np

from   fsl.transform import affine
import fsl.data.image    as fslimage


USAGE = """
Usage: fslchpixdim <hdrfile> <xdim> <ydim> <zdim> [tdim [outfile]] (in mm, or seconds for tdim)
Passing 0 for any dimension will cause the existing value to be used.
""".strip()


def adjustAffine(img  : fslimage.Image,
                 xdim : float,
                 ydim : float,
                 zdim : float) -> np.ndarray:
    """Adjusts the voxel->world transformation of the given image
    to take into account the new pixdims/scaling factors.
    """

    oldxdim, oldydim, oldzdim = img.pixdim[:3]

    xform = img.getAffine('voxel', 'world')
    scale = affine.scaleOffsetXform((
        xdim / oldxdim,
        ydim / oldydim,
        zdim / oldzdim))
    return affine.concat(scale, xform)


def fslchpixdim(img  : fslimage.Image,
                xdim : float = None,
                ydim : float = None,
                zdim : float = None,
                tdim : float = None) -> fslimage.Image:
    """Changes the x/y/z/t dimension sizes of the given image."""

    if xdim is None or xdim == 0: xdim = img.pixdim[0]
    if ydim is None or ydim == 0: ydim = img.pixdim[1]
    if zdim is None or zdim == 0: zdim = img.pixdim[2]

    zooms = [xdim, ydim, zdim]

    if img.ndim >= 4:
        if tdim is None or tdim == 0:
            tdim = img.pixdim[3]
        zooms.append(tdim)
        if img.ndim > 4:
            zooms.extend(img.pixdim[4:])

    xform = adjustAffine(img, *zooms[:3])
    hdr   = img.header.copy()
    hdr.set_zooms(zooms)

    return fslimage.Image(img.data[:], header=hdr, xform=xform)


def main(argv=None):
    """``fslchpixdim`` entry point. Reads command line arguments, calls
    the :func:`fslchpixdim` function.
    """

    if argv is None:
        argv = sys.argv[1:]

    if len(argv) not in (4, 5, 6):
        print(USAGE)
        return 1

    try:
        infile  = argv[0]
        outfile = argv[0]
        xdim    = float(argv[1])
        ydim    = float(argv[2])
        zdim    = float(argv[3])
        tdim    = None

        if len(argv) >= 5: tdim    = float(argv[4])
        if len(argv) == 6: outfile = argv[5]

        inimg  = fslimage.Image(infile)
        outimg = fslchpixdim(inimg, xdim, ydim, zdim, tdim)
        outimg.save(outfile)

    except Exception as e:
        raise e
        print(f'fslchpixdim error: {e}')
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
