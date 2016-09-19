import re
import numpy
import PIL

from .tif import load_tif


def parse_txt(prefix):
    """Read the andor text file"""
    sectionre = re.compile('^\[(?P<section>.*?)(?P<end> End)?\]\n$')
    keyvaluere = re.compile('^(?P<key>.*?)=(?P<value>.*)$')
    framere = re.compile('^\t\tRepeat - (?P<count>[0-9]*) times$', re.MULTILINE)
    parsed = dict()  # the dictionary holding all parsed data
    pointer = parsed  # points to where to insert the parsed data
    stack = []  # resolves the stack of entries of the dictionary
    header = True
    with open(prefix + ".txt") as txt:
        for line in txt.readlines():
            line = line.replace('\r', '')
            match = sectionre.search(line)

            if match:
                header = False
                if match.group('end'):
                    # there is a typo in the end section for pippete......
                    assert (match.group('section') == stack.pop() or "Pippet" in match.group('section'))
                    # print stack
                    pointer = parsed
                    for s in stack:
                        pointer = pointer[s]
                else:
                    stack.append(match.group('section'))
                    pointer[match.group('section')] = dict()
                    # print stack
                    pointer = parsed
                    for s in stack:
                        pointer = pointer[s]
            else:
                match = keyvaluere.search(line)
                if match:
                    pointer[match.group('key')] = match.group('value')
                elif len(line) == 1:
                    pass  # print "<empty>"
                elif header:
                    prefix = pointer['header'] if 'header' in pointer.keys() else ''
                    pointer['header'] = prefix + line
                elif stack[-1] == 'Channel Description' or stack[-1] == 'Protocol Description':
                    key = stack[-1]
                    # delete the dict child entry, and directly write the protocol to the root dictionary
                    if type(parsed[key]) == dict:
                        parsed[key] = ''
                    parsed[key] = parsed[key] + line
                else:
                    raise Exception("Unexpected line in textfile:" + line)
    for match in framere.finditer(parsed['Protocol Description']):
        assert (not 'Frames' in parsed.keys())
        parsed['Frames'] = int(match.group('count'))
    return parsed


def load_andor(prefix):
    """
    todo fixme
        return the data of the tif file as numpy array
        it will have the shape (X,Y,N) where
        - X denotes the coordinate from left to right
        - Y denotes the coordinate from top to bottom
        - N denotes the frames
        return tuple of data, parsed dictionary
    """
    data = load_tif(prefix + ".tif")
    parsed = parse_txt(prefix)
    T = parsed['Frames']
    X = int(parsed['Grab Parameters']['Image Width'])
    Y = int(parsed['Grab Parameters']['Image Height'])

    if data.shape != (Y, X, T):
        print "Shape of txt file doesnt match tif file"
        raise Exception("Shape of txt file {}x{}x{} doesnt match tif file shape {}x{}x{}".format(Y, X, T, *data.shape))
    return data, parsed
