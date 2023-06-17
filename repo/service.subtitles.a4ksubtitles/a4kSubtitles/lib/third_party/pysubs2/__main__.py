import sys
from .cli from .lib.third_party import pysubs2CLI

if __name__ == "__main__":
    cli = Pysubs2CLI()
    rv = cli(sys.argv[1:])
    sys.exit(rv)
