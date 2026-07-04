#!/usr/bin/env python3

import sys

def escape_for_c(s):
    l = [c if c.isalnum() or c in ' .,' else '\\%03o' % ord(c) for c in s]
    return ''.join(l)

if len(sys.argv) != 3:
    print('usage: ' + sys.argv[0] + ' <infile> <outfile>', file=sys.stderr)
    sys.exit(1)

infile = sys.argv[1]
outfile = sys.argv[2]

records = {}

with open(infile, 'r') as f:
    for line in f:
        if line.startswith(" ") or line.startswith("\t"):
            continue

        parts = line.split(maxsplit=2)
        if len(parts) != 3:
            continue

        [oui, kind, name] = parts
        if kind != "(hex)":
            continue

        if len(oui) != 8:
            print(f"Warning: skipping invalid OUI {oui}", file=sys.stderr)
            continue
        oui = int(oui.replace("-", ""), 16)

        records[oui] = escape_for_c(name.strip())

with open(outfile, 'w') as f:
    f.write(
f'''
#include <string.h>
#include <stdint.h>

const char *
_di_get_oui_name(uint8_t oui[static 3]);

const char *
_di_get_oui_name(uint8_t oui[static 3])
{{
    uint32_t u32 = (uint32_t)(((uint32_t)oui[0] << 16) |
                              ((uint32_t)oui[1] << 8) |
                              (uint32_t)oui[2]);

    switch (u32) {{
''')
    for oui in sorted(records.keys()):
        f.write(f'    case {hex(oui)}: return "{records[oui]}";\n')
    f.write(
f'''
    default:
        return NULL;
    }}
}}
''')
