from osc.pythonosc import osc_packet
import slip

def extract_to_file(inf, outf):
    dgrams = slip.decode_file(inf)
    packets = [osc_packet.OscPacket(x) for x in dgrams]
    for i, x in enumerate(packets):
        if len(x.messages) != 1:
            raise ValueError("Packet {} does not have exactly 1 message")
    with open(outf, 'w') as file_:
        for packet in packets:
            for timed in packet.messages:
                file_.write("{} {} {}\n".format(timed.time,
                                                timed.message.address,
                                                timed.message.params))
