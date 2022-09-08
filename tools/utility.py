import re


# quote HTML metacharacters
def q(x):
    return x \
        .replace('&', '&amp;') \
        .replace('>', '&gt;') \
        .replace('<', '&lt;')\
        .replace('"', '&quot;')


# encode parameters as a URL
Q = re.compile(r'[^a-zA-Z0-9_.-=]')


def url(base, **kw):
    r = []
    for (k, v) in kw.iteritems():
        v = Q.sub(lambda m: '%%%02X' % ord(m.group(0)),
                  q(v).encode("utf-8", 'replace')[0])
        r.append('%s=%s' % (k, v))
    return base+'&'.join(r)