import json
import sys


with open("configs/cosr-ops.prod.json") as f:
    CONFIG = json.load(f)


if __name__ == '__main__':
    try:
        ret_val = CONFIG.get(sys.argv[1])
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        ret_val = ''

    sys.stdout.write("%s\n" % ret_val)
