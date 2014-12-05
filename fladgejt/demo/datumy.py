
from datetime import datetime


def rok(offset):
    now = datetime.today()
    return now.year + (now.month > 7) - 5 + offset

def datum(d, m, y):
    return '%02d.%02d.%04d' % (d, m, rok(y))

def ak_rok(y):
    return '%d/%d' % (rok(y), rok(y+1))
