"""XIO file parser."""
import os
from collections import namedtuple
from osc.pythonosc import osc_bundle, osc_message
import slip

Message = namedtuple('Message', ['address', 'params'])
Bundle = namedtuple('Bundle', ['time', 'message'])


class ParseError(Exception):
    """Base error thrown when a datagram could not be parsed."""


def process(dgram):
    """Process datagram to OSC bundle or message."""
    try:
        if osc_bundle.OscBundle.dgram_is_bundle(dgram):
            return osc_bundle.OscBundle(dgram)
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
        self.addresses = set([bundle.message.address for bundle in
                              self.bundles])

    @classmethod
    def from_file(cls, file_):
        """Extract data from XIO file."""
        dgrams = slip.decode_file(file_)
        proc = [process(x) for x in dgrams]
        oscmessages = [x for x in proc if isinstance(x, osc_message.OscMessage)]
        oscbundles = [x for x in proc if isinstance(x, osc_bundle.OscBundle)]
        messages = [Message(msg.address, msg.params) for msg in oscmessages]
        for bundle in oscbundles:
            if bundle.num_contents != 1 or \
               not isinstance(bundle.content(0), osc_message.OscMessage):
                raise ValueError("XIO OSC bundle should contain"
                                 "a single OSC message.")
        bundles = [(bundle.timestamp, bundle.content(0))
                   for bundle in oscbundles]
        bundles = [Bundle(time, Message(msg.address, msg.params))
                   for time, msg in bundles]
        return cls(messages, bundles)

    def dump(self, out):
        """Dump data to file."""
        with open(out, 'w') as file_:
            for message in self.messages:
                file_.write("# {} {}\n".format(*message))
            for bundle in self.bundles:
                file_.write("{} {} {}\n".format(*bundle))

    def to_csv(self, out, addr):
        """Output csv file containing data from bundles with given address."""
        with open(out, 'w') as file_:
            for bundle in self.bundles:
                if bundle.message.address == addr:
                    vals = ','.join([str(x) for x in [bundle.time,
                                                      *bundle.message.params]])
                    file_.write("{}\n".format(vals))

    def to_dir(self, dirname):
        """Write to directory."""
        os.makedirs(dirname, exist_ok=True)
        for addr in self.addresses:
            if addr[0] != '/':
                raise ValueError("Unrecognized address form {}.".format(addr))
            filename = os.path.join(dirname,
                                    addr.strip('/').replace('/', '.') + '.csv')
            self.to_csv(filename, addr)
