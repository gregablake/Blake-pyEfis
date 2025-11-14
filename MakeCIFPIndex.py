#!/usr/bin/env python3
"""
MakeCIFPIndex.py - Create a binary index for the FAA CIFP file (FAACIFP18)

Usage:
    ./MakeCIFPIndex.py CIFP/FAACIFP18

This script scans the FAACIFP18 file and creates an index.bin file in the same directory.
The index allows pyEfis to quickly look up records by airport, navaid, or fix name.
"""
import sys
import os
import struct

INDEX_FILENAME = "index.bin"

# Example: index by record type and identifier (first 4 chars: record type, next 30: id)
def parse_cifp_line(line):
    # FAA CIFP lines are fixed-width, see FAA docs for details
    record_type = line[0:4].strip()
    ident = line[4:34].strip()
    return record_type, ident

def main():
    if len(sys.argv) != 2:
        print("Usage: ./MakeCIFPIndex.py CIFP/FAACIFP18")
        sys.exit(1)
    cifp_path = sys.argv[1]
    if not os.path.isfile(cifp_path):
        print(f"File not found: {cifp_path}")
        sys.exit(1)
    index = {}
    with open(cifp_path, "r", encoding="utf-8", errors="ignore") as f:
        offset = 0
        for line in f:
            record_type, ident = parse_cifp_line(line)
            if ident:
                # Store offset for each unique (type, id)
                index[(record_type, ident)] = offset
            offset += len(line)
    # Write index to binary file
    index_path = os.path.join(os.path.dirname(cifp_path), INDEX_FILENAME)
    with open(index_path, "wb") as idx:
        for (record_type, ident), offset in index.items():
            # Write as: 4s 30s Q (type, id, offset)
            idx.write(struct.pack("4s30sQ", record_type.encode("ascii", "ignore")[:4].ljust(4, b' '),
                                             ident.encode("ascii", "ignore")[:30].ljust(30, b' '),
                                             offset))
    print(f"Index written to {index_path} ({len(index)} entries)")

if __name__ == "__main__":
    main()
