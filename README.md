# pybind - command line utilities for book binders

## perfect binding : perfect.py
perfect.py takes a standard pdf and formats it as a booklet, such that you can cut the pages in half, stack the two halves, and end up with a single, half-sheed sized book. 

usage: 
    $ python perfect.py -i <input.pdf> [-o <output.pdf>] [-p <page-size>] [-s <scale>]

    where page-size is LETTER or A4, and scale is a number between 0 and 1

    only the input.pdf is required, others will default to default values
