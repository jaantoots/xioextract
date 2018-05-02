"""XIO file parser."""
from osc.pythonosc import osc_bundle, osc_message
import slip

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


def extract_to_file(inf, outf):
    """Extract data from XIO file."""
    dgrams = slip.decode_file(inf)
    proc = [process(x) for x in dgrams]
    bundles = [x for x in proc if isinstance(x, osc_bundle.OscBundle)]
    messages = [x for x in proc if isinstance(x, osc_message.OscMessage)]

    with open(outf, 'w') as file_:
        for message in messages:
            file_.write("# {} {}\n".format(message.address, message.params))
        for bundle in bundles:
            if bundle.num_contents != 1 or \
               not isinstance(bundle.content(0), osc_message.OscMessage):
                raise ValueError("XIO OSC bundle should contain"
                                 "a single OSC message.")
            message = bundle.content(0)
            file_.write("{} {} {}\n".format(bundle.timestamp,
                                            message.address,
                                            message.params))
