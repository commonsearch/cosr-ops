import json
import sys
import os


if not os.path.isfile("configs/cosr-ops.prod.json"):
    sys.exit(0)


with open("configs/cosr-ops.prod.json") as f:
    CONFIG = json.load(f)


if __name__ == '__main__':
    try:
        ret_val = CONFIG.get(sys.argv[1]) or ''
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        ret_val = ''

    sys.stdout.write("%s\n" % ret_val)
