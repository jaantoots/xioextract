"""XIO file parser."""
import os
import argparse
from osc.pythonosc import osc_bundle, osc_message
import slip


class ParseError(Exception):
    """Base error thrown when a datagram could not be parsed."""


def process(dgram):
    """Process datagram to OSC bundle or message."""
    try:
        if osc_bundle.OscBundle.dgram_is_bundle(dgram):
            bundle = osc_bundle.OscBundle(dgram)
            if bundle.num_contents != 1 or \
               not isinstance(bundle.content(0), osc_message.OscMessage):
                raise ValueError("XIO OSC bundle should contain"
                                 "a single OSC message.")
            return bundle
        elif osc_message.OscMessage.dgram_is_message(dgram):
            return osc_message.OscMessage(dgram)
        else:
            # Empty packet, should not happen as per the spec but heh, UDP...
            raise ParseError("Datagram should at least contain"
                             "an OscMessage or an OscBundle.")
    except (osc_bundle.ParseError, osc_message.ParseError) as error:
        raise ParseError("Could not parse packet {:s}".format(error))


class XIOData():
    """Data extraction from XIO files."""

    def __init__(self, messages, bundles):
        """Initialize data."""
        self.messages = messages
        self.bundles = bundles
        self.addresses = set(bundle[1] for bundle in self.bundles)

    @classmethod
    def from_file(cls, file_):
        """Extract data from XIO file."""
        proc = [process(x) for x in slip.decode_file(file_)]
        messages, bundles = [], []
        for pkt in proc:
            if isinstance(pkt, osc_bundle.OscBundle):
                msg = pkt.content(0)
                bundles.append((pkt.timestamp, msg.address, msg.params))
            else:
                if bundles:
                    yield cls(messages, bundles)
                    messages, bundles = [], []
                messages.append((pkt.address, pkt.params))
        yield cls(messages, bundles)

    def dump(self, out):
        """Dump data to file."""
        with open(out, 'w') as file_:
            for message in self.messages:
                file_.write("# {} {}\n".format(*message))
            for bundle in self.bundles:
                file_.write("{} {} {}\n".format(*bundle))

    def messages_unpack(self):
        """Unpack messages for output."""
        for message in self.messages:
            yield [message[0], *message[1]]

    def bundles_unpack(self, addr):
        """Unpack bundles with given address for output."""
        for bundle in self.bundles:
            if bundle[1] == addr:
                yield [bundle[0], *bundle[2]]

    @staticmethod
    def to_csv(out, gen):
        """Output csv file containing unpacked values from generator."""
        with open(out, 'w') as file_:
            for vals in gen:
                csv = ','.join([str(x) for x in vals])
                file_.write("{}\n".format(csv))

    def to_dir(self, dirname):
        """Write to directory."""
        os.makedirs(dirname, exist_ok=True)
        if self.messages:
            filename = os.path.join(dirname, 'settings.csv')
            self.to_csv(filename, self.messages_unpack())
        for addr in self.addresses:
            if addr[0] != '/':
                raise ValueError("Unrecognized address format {}.".format(addr))
            filename = os.path.join(dirname,
                                    addr.strip('/').replace('/', '.') + '.csv')
            self.to_csv(filename, self.bundles_unpack(addr))

def main():
    """Convert XIO to CSV."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xio", type=str,
                        help="Input XIO file")
    parser.add_argument("out", type=str,
                        help="Output directory")
    args = parser.parse_args()

    for i, data in enumerate(XIOData.from_file(args.xio)):
        data.to_dir(os.path.join(args.out, str(i)))

if __name__ == "__main__":
    main()
