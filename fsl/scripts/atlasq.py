#!/usr/bin/env python
#
# main.py - The atlasq program.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains the FSL ``atlasq`` program, the successor to
``atlasquery``.
"""


from __future__ import print_function

import itertools as it
import              sys
import              argparse
import              textwrap
import              warnings
import              logging
import numpy     as np

# if h5py <= 2.7.1 is installed,
# it will be imported via nibabel,
# and will cause a numpy warning
# to be emitted.
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=FutureWarning)
    import fsl.data.image as fslimage

# If wx is not present, then fsl.utils.platform
# will complain that it is not present.
logging.getLogger('fsl.utils.platform').setLevel(logging.ERROR)

import fsl.data.atlases as fslatlases  # noqa
import fsl.version      as fslversion  # noqa


log = logging.getLogger(__name__)


SHORT_QUERY_DELIM = '\t'


class IdentifyError(Exception):
    """Exception raised by the ``identifyAtlas`` when an atlas cannot be
    identified.
    """
    pass


class HelpFormatter(argparse.RawDescriptionHelpFormatter):
    """A custom ``argparse.HelpFormatter`` class which customises a few
    annoying things about default ``argparse`` behaviour.
    """
    def _format_usage(self, usage, actions, groups, prefix):

        # Inhibit the 'usage: ' prefix
        return argparse.RawDescriptionHelpFormatter._format_usage(
            self, usage, actions, groups, '')


def listAtlases(namespace):
    """List all available atlases. """
    atlases = fslatlases.listAtlases()

    if namespace.extended:
        for a in atlases:
            print('{} [{}]'.format(a.name, a.atlasID))
            print('  Spec:          {}'.format(a.specPath))
            print('  Type:          {}'.format(a.atlasType))
            print('  Labels:        {}'.format(len(a.labels)))
            for i in a.images:
                print('  Image:         {}'.format(i))
            for i in a.summaryImages:
                print('  Summary image: {}'.format(i))
            print()

    else:
        ids   = [a.atlasID for a in atlases]
        names = [a.name    for a in atlases]

        printColumns((ids, names), ('ID', 'Full name'))


def summariseAtlas(namespace):
    """Print information about one atlas. """

    a = identifyAtlas(namespace.atlas)
    print('{} [{}]'.format(a.name, a.atlasID))
    print('  Spec:          {}'.format(a.specPath))
    print('  Type:          {}'.format(a.atlasType))
    print('  Labels:        {}'.format(len(a.labels)))
    for i in a.images:
        print('  Image:         {}'.format(i))
    for i in a.summaryImages:
        print('  Summary image: {}'.format(i))

    indices = [l.index for l in a.labels]
    names   = [l.name  for l in a.labels]
    xs      = [l.x     for l in a.labels]
    ys      = [l.y     for l in a.labels]
    zs      = [l.z     for l in a.labels]

    printColumns(( indices, names,   xs,  ys,  zs),
                 ('Index', 'Label', 'X', 'Y', 'Z'))


def queryAtlas(namespace):
    """Query an atlas with coordinates or masks."""

    atlasDesc = identifyAtlas(namespace.atlas)
    wcoords   = namespace.coord
    vcoords   = namespace.voxel
    masks     = [fslimage.Image(m) for m in namespace.mask]
    worder    = namespace.coord_order
    vorder    = namespace.voxel_order
    morder    = namespace.mask_order
    atlas     = fslatlases.loadAtlas(atlasDesc.atlasID,
                                     loadSummary=namespace.label,
                                     resolution=namespace.resolution)

    mlabels, mprops = maskQuery( atlas, masks)
    wlabels, wprops = coordQuery(atlas, wcoords, False)
    vlabels, vprops = coordQuery(atlas, vcoords, True)

    order   = list(it.chain(morder,  worder,   vorder))
    labels  = list(it.chain(mlabels, wlabels,  vlabels))
    props   = list(it.chain(mprops,  wprops,   vprops))
    sources = list(it.chain(masks,   wcoords,  vcoords))
    types   = list(it.chain(['mask']       * len(masks),
                            ['coordinate'] * len(wcoords),
                            ['voxel']      * len(vcoords)))

    labels  = [l for (o, l) in sorted(zip(order, labels))]
    props   = [p for (o, p) in sorted(zip(order, props))]
    sources = [s for (o, s) in sorted(zip(order, sources))]
    types   = [t for (o, t) in sorted(zip(order, types))]

    if namespace.short: queryShortOutput(atlas, sources, types, labels, props)
    else:               queryLongOutput( atlas, sources, types, labels, props)


def queryShortOutput(atlas, sources, types, allLabels, allProps):
    """Called by ``queryAtlas`` when short output is requested. """

    for source, stype, labels, props in zip(sources,
                                            types,
                                            allLabels,
                                            allProps):

        if stype == 'coordinate':
            source = '{:0.2f} {:0.2f} {:0.2f}'.format(*source)
        elif stype == 'voxel':
            source = '{:0.0f} {:0.0f} {:0.0f}'.format(*source)
        elif stype == 'mask':
            source = source.dataSource

        results = []
        labels  = labelNames(atlas, labels)

        # Coordinate lookup for a label
        # atlas just returns a label
        if stype in ('coordinate', 'voxel') and \
           isinstance(atlas, fslatlases.LabelAtlas):
            results.append('{}'.format(labels[0]))

        # All other queries return a list of
        # labels and proportions. We output
        # them from highest proportion to
        # lowest
        else:
            for p, l in reversed(sorted(zip(props, labels))):
                results.append('{} {:0.4f}'.format(l, p))

        print(SHORT_QUERY_DELIM.join([stype, source] + results))


def queryLongOutput(atlas, sources, types, allLabels, allProps):
    """Called by ``queryAtlas`` when long output is requested. """

    def summaryCoord(source, stype, labels, props, names):

        label = labels[0]
        name  = names[ 0]

        if label is None: label = np.nan
        else:             label = int(label)

        fields = ['name', 'index']
        values = [name, label]

        if atlas.desc.atlasType == 'probabilistic':
            fields.append('summary value')
            values.append(label + 1)
        else:
            fields[1] = 'label'

        printColumns((fields, values))


    def proportions(source, stype, labels, props, names):

        if len(labels) == 0:
            print('No results')
            return

        proplabelnames = list(reversed(sorted(zip(props, labels, names))))
        props          = [pln[0] for pln in proplabelnames]
        labels         = [pln[1] for pln in proplabelnames]
        names          = [pln[2] for pln in proplabelnames]
        props          = ['{:0.4f}'.format(p) for p in props]

        titles  = ['name', 'index', 'proportion']
        columns = [ names,  labels,  props]

        if atlas.desc.atlasType == 'probabilistic':
            sumvals = [l + 1 for l in labels]
            titles .insert(2, 'summary value')
            columns.insert(2, sumvals)
        else:
            titles[1] = 'label'

        printColumns(columns, titles)


    for source, stype, labels, props in zip(sources,
                                            types,
                                            allLabels,
                                            allProps):

        if stype == 'coordinate':
            sourcestr = '{:0.2f} {:0.2f} {:0.2f}'.format(*source)
        elif stype == 'voxel':
            sourcestr = '{:0.0f} {:0.0f} {:0.0f}'.format(*source)
        elif stype == 'mask':
            sourcestr = '{}'.format(source.dataSource)

        title = '{} {}'.format(stype, sourcestr)

        print('-' * (4 + len(title)))
        print('| {} |'.format(title))
        print('-' * (4 + len(title)))
        print()

        names = labelNames(atlas, labels)

        if stype in ('coordinate', 'voxel') and \
           isinstance(atlas, fslatlases.LabelAtlas):
            summaryCoord(source, stype, labels, props, names)
        else:
            proportions(source, stype, labels, props, names)
        print()


def ohi(namespace):
    """Emulates the FSL ``atlasquery`` tool."""

    atlasDesc = None

    def dumpatlases():
        atlases = [a.name for a in fslatlases.listAtlases()]
        print('\n'.join(sorted(atlases)))

    if namespace.dumpatlases:
        dumpatlases()
        return

    for a in fslatlases.listAtlases():
        if a.name == namespace.atlas:
            atlasDesc = a
            break

    if atlasDesc is None:
        print('Invalid atlas name. Try one of:')
        dumpatlases()
        return

    # Mask query.
    if namespace.ohiMask is not None:

        # atlasquery always uses 2mm atlas versions
        mask          = fslimage.Image(namespace.ohiMask)
        labels, props = maskQuery(atlasDesc, [mask], resolution=2)
        labels        = labels[0]
        props         = props[ 0]

        for lbl, prop in zip(labels, props):
            lbl = atlasDesc.labels[int(lbl)].name
            print('{}:{:0.4f}'.format(lbl, prop))

    # Coordinate query
    else:
        coord         = namespace.coord.strip('"')
        coord         = [float(c) for c in coord.split(',')]
        labels, props = coordQuery(atlasDesc,
                                   [coord],
                                   False,
                                   resolution=2)

        labels = labels[0]
        props  = props[ 0]

        if atlasDesc.atlasType == 'label':

            labels = labels[0]

            if labels is None: label = 'Unclassified'
            else:              label = atlasDesc.labels[int(labels)].name
            print('<b>{}</b><br>{}'.format(atlasDesc.name, label))

        elif atlasDesc.atlasType == 'probabilistic':

            labelStrs = []

            if len(labels) > 0:
                props, labels = zip(*reversed(sorted(zip(props, labels))))

            for label, prop in zip(labels, props):
                label = atlasDesc.labels[int(label)].name
                labelStrs.append('{:d}% {}'.format(int(round(prop)), label))

            if len(labelStrs) == 0: labels = 'No label found!'
            else:                   labels = ', '.join(labelStrs)

            print('<b>{}</b><br>{}'.format(atlasDesc.name, labels))


def atlasOrDesc(aord, *args, **kwargs):
    """If ``aord`` is an ``Atlas`` it is returned. Otherwise it is assumed to
    be an ``AtlasDescription``, in which case the corresponding ``Atlas`` is
    loaded and returned.
    """
    if isinstance(aord, fslatlases.Atlas):
        return aord
    else:
        return fslatlases.loadAtlas(aord.atlasID, *args, **kwargs)


def labelNames(atlas, labels):
    """Converts the given sequence of ``labels`` into region names. """

    names = []

    for l in labels:
        if l is None: names.append('No label')
        else:         names.append(atlas.desc.labels[int(l)].name)

    return names


def maskQuery(atlas, masks, *args, **kwargs):
    """Queries the ``atlas`` at the given ``masks``. """

    allLabels = []
    allProps  = []
    atlas     = atlasOrDesc(atlas, *args, **kwargs)

    for mask in masks:

        if isinstance(atlas, fslatlases.LabelAtlas):

            labels, props = atlas.maskLabel(mask)

            # We need to subtract 1 from summary
            # image label values to get the label
            # index, for probabilistic atlases.
            if atlas.desc.atlasType == 'probabilistic':
                labels = [l - 1 for l in labels]

        elif isinstance(atlas, fslatlases.ProbabilisticAtlas):

            labels = []
            props  = []
            zprops = atlas.maskProportions(mask)

            for i in range(len(zprops)):
                if zprops[i] > 0:
                    props.append(zprops[i])
                    labels.append(atlas.desc.labels[i].index)

        allLabels.append(labels)
        allProps .append(props)

    return allLabels, allProps


def coordQuery(atlas, coords, voxel, *args, **kwargs):
    """Queries the ``atlas`` at the given ``coords``. """

    atlas     = atlasOrDesc(atlas, *args, **kwargs)
    allLabels = []
    allProps  = []

    for coord in coords:

        if isinstance(atlas, fslatlases.ProbabilisticAtlas):

            props   = atlas.proportions(coord, voxel=voxel)
            labels  = []
            nzprops = []

            for i, p in enumerate(props):
                if p != 0:
                    nzprops.append(p)
                    labels .append(atlas.desc.labels[i].index)

            allLabels.append(labels)
            allProps .append(nzprops)

        elif isinstance(atlas, fslatlases.LabelAtlas):

            label = atlas.label(coord, voxel=voxel)

            # we need to subtract 1 from the label
            # value to get the label index, for
            # probabilistic summary images.
            if atlas.desc.atlasType == 'probabilistic':

                # 0 == background
                if label == 0:        label = None
                if label is not None: label = label - 1

            allLabels.append([label])
            allProps .append([None])

    return allLabels, allProps


def identifyAtlas(idOrName):
    """Given a partial atlas ID or name, tries to find an atlas which
    uniquely matches it.
    """

    # TODO Use difflib or some fuzzy matching library?

    idOrName = idOrName.lower().strip()
    atlases  = fslatlases.listAtlases()

    allNames = [a.name   .lower() for a in atlases]
    allIDs   = [a.atlasID.lower() for a in atlases]

    # First test for an exact match
    nameMatches = [idOrName == n for n in allNames]
    idMatches   = [idOrName == i for i in allIDs]

    nameMatches = [i for i in range(len(nameMatches)) if nameMatches[i]]
    idMatches   = [i for i in range(len(idMatches))   if idMatches[  i]]

    if len(nameMatches) + len(idMatches) == 1:
        if len(nameMatches) == 1: return atlases[nameMatches[0]]
        else:                     return atlases[idMatches[  0]]

    # If no exact match, test for a partial match
    nameMatches = [idOrName in n for n in allNames]
    idMatches   = [idOrName in i for i in allIDs]

    nameMatches = [i for i in range(len(nameMatches)) if nameMatches[i]]
    idMatches   = [i for i in range(len(idMatches))   if idMatches[  i]]

    totalMatches = len(nameMatches) + len(idMatches)

    # No matches
    if totalMatches == 0:
        raise IdentifyError('Could not find any atlas '
                            'matching {}'.format(idOrName))

    # More than two matches, or a
    # different ID/name pair matched
    if totalMatches > 2 or (totalMatches == 2 and nameMatches != idMatches):

        possible = [allNames[m] for m in nameMatches] + \
                   [allIDs[  m] for m in idMatches]

        raise IdentifyError('{} matched multiple atlases! Could match one '
                            'of: {}'.format(idOrName, ', '.join(possible)))

    # Either one exact match to an ID or name,
    # or a match to an equivalent ID/name
    if len(nameMatches) == 1: return atlases[nameMatches[0]]
    else:                     return atlases[idMatches[  0]]


def printColumns(columns, titles=None, delim=' | ', sep=True, strip=False):
    """Convenience function which pretty-prints a collection of columns in a
    tabular format.

    :arg columns: A sequence of columns, where each column is a list of
                  strings.

    :arg titles:  A sequence of titles, one for each column.
    """

    if len(columns) == 0:
        return

    columns = list(columns)

    for i, c in enumerate(columns):
        col = list(map(str, c))
        if titles is not None: columns[i] = [titles[i]] + col
        else:                  columns[i] =               col

    colLens = []
    for col in columns:
        maxLen = max([len(r) for r in col])
        colLens.append(maxLen)

    fmtStr = delim.join(['{{:<{}s}}'.format(l) for l in colLens])

    if titles is not None and sep:
        titles    = [col[0]  for col in columns]
        columns   = [col[1:] for col in columns]
        separator = ['-' * l for l in colLens]

        print(fmtStr.format(*titles))
        print(fmtStr.format(*separator))

    nrows = len(columns[0])
    for i in range(nrows):

        row = [col[i] for col in columns]
        row = fmtStr.format(*row)
        if strip:
            row = row.strip()

        print(row)


def parseArgs(args):
    """Parses command line arguments, returning an ``argparse.Namespace``
    object.
    """

    # Show help if no args are provided
    if  len(args) == 0 or \
       (len(args) == 1 and args[0] in ('ohi', 'summary', 'query')):
        args = list(args) + ['-h']

    # Hack to make argparse accept
    # coordinates with a negative sign
    # (ohi/atlasquery interface only)
    if args[0] == 'ohi':
        try:
            cidx           = args.index('-c')
            coord          = args[cidx + 1]
            args[cidx + 1] = '"{}"'.format(coord)
        except:
            pass

    prolog = 'FSL atlasq {}'.format(fslversion.__version__)

    helps = {
        'ohi'     : 'Emulate the FSL atlasquery tool',
        'list'    : 'List available atlases',
        'summary' : 'Print a summary of one atlas',
        'query'   : 'Query an atlas at specific coordinates'
    }

    usages = {
        'main'    : 'usage: atlasq [-h] command [options]',
        'ohi'     : textwrap.dedent("""
                     usage: atlasq ohi -h
                            atlasq ohi --dumpatlases
                            atlasq ohi -a atlas -c X,Y,Z
                            atlasq ohi -a atlas -m mask
        """).strip(),
        'list'    : 'usage: atlasq list [-e]',
        'summary' : 'usage: atlasq summary atlas',
        'query' : textwrap.dedent("""
                     usage: atlasq query atlas [options] -m mask  [-m mask ...]
                     usage: atlasq query atlas [options] -c X Y Z [-c X Y Z...]
                     usage: atlasq query atlas [options] -v X Y Z [-v X Y Z...]
                     usage: atlasq query atlas [options] -v X Y Z \\
                                                        [-c X Y Z [-m mask]...]
        """).strip(),
    }

    for k in usages:
        usages[k] = '{}\n\n{}'.format(prolog, usages[k])

    parser = argparse.ArgumentParser(
        prog='atlasq',
        usage=usages['main'],
        formatter_class=HelpFormatter)

    subParsers = parser.add_subparsers(title='Commands', dest='command')
    ohiParser = subParsers.add_parser(
        'ohi',
        help=helps['ohi'],
        usage=usages['ohi'],
        formatter_class=HelpFormatter)
    listParser = subParsers.add_parser(
        'list',
        help=helps['list'],
        usage=usages['list'],
        formatter_class=HelpFormatter)
    sumParser = subParsers.add_parser(
        'summary',
        help=helps['summary'],
        usage=usages['summary'],
        formatter_class=HelpFormatter)
    queryParser = subParsers.add_parser(
        'query',
        help=helps['query'],
        usage=usages['query'],
        formatter_class=HelpFormatter)

    # This is a custom argparse.Action used by the
    # query command parser which keeps track of the
    # order in which query arguments are passed. The
    # three query types (mask, voxel, coord) are
    # each added to separate lists. For each type, a
    # second list (called mask_order, voxel_order,
    # and coord_order) is maintained which stores
    # the index of each query across all types.
    class QueryAction(argparse.Action):

        queryCount = 0

        def __init__(self, *args, **kwargs):
            argparse.Action.__init__(self, *args, **kwargs)

        def __call__(self, parser, namespace, values, option_string=None):

            dest  = getattr(namespace,                   self.dest,  None)
            order = getattr(namespace, '{}_order'.format(self.dest), None)

            if dest  is None: dest  = []
            if order is None: order = []

            dest .append(values)
            order.append(QueryAction.queryCount)

            setattr(namespace,                   self.dest,  dest)
            setattr(namespace, '{}_order'.format(self.dest), order)

            QueryAction.queryCount += 1


    # OldHorribleInterface parser
    ohiParser.add_argument(
        '-a', '--atlas',
        help='Name of atlas to use')
    ohiParser.add_argument(
        '-V', '--verbose',
        action='store_true',
        help='Switch on diagnostic messages')
    ohiSubParser = ohiParser.add_mutually_exclusive_group()
    ohiSubParser.add_argument(
        '-m', '--mask',
        dest='ohiMask',
        metavar='MASK',
        help='A mask image to use during structural lookups')
    ohiSubParser.add_argument(
        '-c', '--coord',
        help='Coordinate to query')
    ohiParser.add_argument(
        '--dumpatlases',
        action='store_true',
        help='Dump a list of the available atlases')

    # List parser
    listParser.add_argument(
        '-e', '--extended',
        action='store_true',
        help='Print more information about each atlas')

    # Summary parser
    sumParser.add_argument('atlas', help='Name or ID of atlas to summarise')

    # Query parser
    queryParser.add_argument(
        'atlas',
        help='Name or ID of atlas to summarise.')
    queryParser.add_argument(
        '-r', '--resolution',
        type=float,
        help='Desired atlas resolution (mm). Default is highest available '
             'resolution.')
    queryParser.add_argument(
        '-s', '--short',
        action='store_true',
        help='Output in short (machine-friendly) format.')
    queryParser.add_argument(
        '-l', '--label',
        action='store_true',
        help='Query label/maxprob version of atlas (for probabilistic '
             'atlases).')
    queryParser.add_argument(
        '-m', '--mask',
        action=QueryAction,
        help='Mask to query with.')
    queryParser.add_argument(
        '-c', '--coord',
        nargs=3,
        type=float,
        metavar=('X', 'Y', 'Z'),
        action=QueryAction,
        help='World coordinates to look up.')
    queryParser.add_argument(
        '-v', '--voxel',
        nargs=3,
        type=float,
        metavar=('X', 'Y', 'Z'),
        action=QueryAction,
        help='Voxel coordinates to look up. Must be in terms of the atlas '
        'at the specified (or default) --resolution.')

    namespace = parser.parse_args(args)

    if namespace.command != 'query':
        return namespace

    # Make life easier for the queryAtlas code
    if namespace.mask  is None:               namespace.mask        = []
    if namespace.coord is None:               namespace.coord       = []
    if namespace.voxel is None:               namespace.voxel       = []
    if not hasattr(namespace, 'mask_order'):  namespace.mask_order  = []
    if not hasattr(namespace, 'coord_order'): namespace.coord_order = []
    if not hasattr(namespace, 'voxel_order'): namespace.voxel_order = []

    return namespace


def main(args=None):
    """Entry point for ``atlasq``. Parses arguments, and runs the requested
    command.
    """

    if args is None:
        args = sys.argv[1:]

    # Parse command line arguments
    namespace = parseArgs(args)

    # Initialise the atlas library
    fslatlases.rescanAtlases()

    # Run the command
    try:
        if   namespace.command == 'list':    listAtlases(   namespace)
        elif namespace.command == 'query':   queryAtlas(    namespace)
        elif namespace.command == 'summary': summariseAtlas(namespace)
        elif namespace.command == 'ohi':     ohi(           namespace)

    except (IdentifyError, fslatlases.MaskError) as e:
        print(str(e))
        return 1

    return 0


def atlasquery_emulation(args=None):
    """Entry point for ``atlasquery``. Runs as ``atlasq`` in ``ohi``
    mode.
    """

    if args is None:
        args = sys.argv[1:]

    return main(['ohi'] + args)


if __name__ == '__main__':
    sys.exit(main())
