"""Encode and decode datagrams in SLIP.

Inspired by https://github.com/mehdisadeghi/pyslip
"""
SLIP_END = b'\xc0'
SLIP_ESC = b'\xdb'
SLIP_ESC_END = b'\xdb\xdc'
SLIP_ESC_ESC = b'\xdb\xdd'

def slip_encode(dgrams):
    """Encode a list of bytes as SLIP bytes."""
    return SLIP_END.join(
        [x.replace(SLIP_ESC, SLIP_ESC_ESC).replace(SLIP_END, SLIP_ESC_END)
         for x in dgrams]) + SLIP_END

def slip_decode(data):
    """Decode SLIP bytes to list of datagrams."""
    return [x.replace(SLIP_ESC_END, SLIP_END).replace(SLIP_ESC_ESC, SLIP_ESC)
            for x in data.strip(SLIP_END).split(SLIP_END)]

def decode_file(filename):
    """Decode file to list of datagrams."""
    with open(filename, 'rb') as file_:
        # Careful with large files
        data = file_.read()
    return slip_decode(data)
