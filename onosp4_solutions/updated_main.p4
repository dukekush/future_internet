#include <core.p4>
#include <v1model.p4>

#define CPU_PORT 255
#define CPU_CLONE_SESSION_ID 99

typedef bit<9>   port_num_t;
typedef bit<48>  mac_addr_t;
typedef bit<32>  ipv4_addr_t;


const bit<16> ETHERTYPE_IPV4    = 0x0800;

// Exercise 2 TO-DO: Define a symbolic constant for ARP ethertype

const bit<16> ETHERTYPE_ARP = 0x0806; // ARP Ethertype
const bit<16> ARP_HTYPE = 0x0001; // Ethernet Hardware type
const bit<16> ARP_PTYPE = 0x0800; // IPv4 Protocol type
const bit<8> ARP_HLEN = 6; // Hardware Length for Ethernet
const bit<8> ARP_PLEN = 4; // Protocol Length for IPv4
const bit<16> ARP_OPER_REQUEST = 0x0001; // ARP Request operation code
const bit<16> ARP_OPER_REPLY = 0x0002; // ARP Reply operation code



//+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
//+++++++++++++++++++++++++++ HEADER DEFINITIONS ++++++++++++++++++++++++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

header ethernet_t {
        mac_addr_t  dst_addr;
        mac_addr_t  src_addr;
        bit<16>    ether_type;
}


header arp_t {
    bit<16> htype;
    bit<16> ptype;
    bit<8> hlen;
    bit<8> plen;
    bit<16> oper;
    mac_addr_t sha;
    ipv4_addr_t spa;
    mac_addr_t tha;
    ipv4_addr_t tpa;
}


header ipv4_t {
        bit<4>    version;
        bit<4>    ihl;
        bit<6>    dscp;
        bit<2>    ecn;
        bit<16>   total_len;
        bit<16>   identification;
        bit<3>    flags;
        bit<13>   frag_offset;
        bit<8>    ttl;
        bit<8>    protocol;
        bit<16>   hdr_checksum;
        ipv4_addr_t src_addr;
        ipv4_addr_t dst_addr;
}


@controller_header("packet_in")
header cpu_in_header_t {
        port_num_t  ingress_port;
        bit<7>      _pad;
}

@controller_header("packet_out")
header cpu_out_header_t {
        port_num_t  egress_port;
        bit<7>      _pad;
}

        
struct parsed_headers_t {
    ethernet_t ethernet;
    arp_t arp; // Added ARP header
    ipv4_t ipv4;
    cpu_out_header_t cpu_out;
    cpu_in_header_t cpu_in;
}


struct local_metadata_t {
        @field_list(1)
        bit<9>    port1;
        bit<9>    port2;
}


//+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
//+++++++++++++++++++++++++++++++++ PARSER ++++++++++++++++++++++++++++++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


parser ParserImpl (packet_in packet,
                   out parsed_headers_t hdr,
                   inout local_metadata_t local_metadata,
                   inout standard_metadata_t standard_metadata){

        state start {
                transition select(standard_metadata.ingress_port) {
                        CPU_PORT: parse_packet_out;
                        default: parse_ethernet;
                }
        }

        state parse_packet_out {
                packet.extract(hdr.cpu_out);
                transition parse_ethernet;
        }

        /*
                Exercise 2 TO-DO: Perform three changes to the parse_ethernet
                state:
                1. Create a transition selection based on the ether_type field
                   of the ethernet header
                2. For IPv4 packets, transition to the parse_ipv4 state
                3. For ARP packets, trasition to the parse_arp state.
                Note: Leave the parse_ipv4 state as default transition
        */

        
        state parse_ethernet {
                packet.extract(hdr.ethernet);
                transition select(hdr.ethernet.ether_type) {
                        ETHERTYPE_IPV4: parse_ipv4;
                        ETHERTYPE_ARP: parse_arp;
                        default: parse_ipv4;
                }
        }


        state parse_ipv4 {
                packet.extract(hdr.ipv4);
                transition accept;
        }

        /*
                Exercise 2 TO-DO: Define the parse_arp state which should
                perform the following two things:
                1. Extract the arp header from the packet
                2. Create a transition selection based on the ARP Operation
                   code in such a way that only ARP requestes get accepted
        */

        state parse_arp {
                packet.extract(hdr.arp);
                transition select(hdr.arp.oper) {
                        ARP_OPER_REQUEST: accept;
                }
        }
}

//+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
//++++++++++++++++++++++++++++++++ CHECKSUM +++++++++++++++++++++++++++++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

control VerifyChecksumImpl(inout parsed_headers_t hdr,
                           inout local_metadata_t local_metadata){

        apply { /* EMPTY */ }
}

//+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
//+++++++++++++++++++++++++++ INGRESS PROCESSING ++++++++++++++++++++++++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

control IngressPipeImpl(inout parsed_headers_t    hdr,
                        inout local_metadata_t    local_metadata,
                        inout standard_metadata_t standard_metadata){

        // --- DROP  -----------------------------------------------------------
        action drop() {
                mark_to_drop(standard_metadata);
        }

        // --- CPU  ------------------------------------------------------------
        action send_to_cpu() {
                standard_metadata.egress_spec = CPU_PORT;
        }

        action clone_to_cpu() {
                clone_preserving_field_list(CloneType.I2E, CPU_CLONE_SESSION_ID,1);
        }

        // --- ACL TABLE  ------------------------------------------------------

        table acl_table {
                key = {
                        standard_metadata.ingress_port: ternary;
                        hdr.ethernet.dst_addr:          ternary;
                        hdr.ethernet.src_addr:          ternary;
                        hdr.ethernet.ether_type:        ternary;
                }

                actions = {
                        send_to_cpu;
                        clone_to_cpu;
                        drop;
                }

                @name("acl_table_counter")
                counters = direct_counter(CounterType.packets_and_bytes);
        }


        // --- l2_exact_table --------------------------------------------------
        action set_egress_port(port_num_t port_num){
                standard_metadata.egress_spec = port_num;
        }



        table l2_exact_table {
                key = {
                        hdr.ethernet.dst_addr: exact;
                }

                actions = {
                        set_egress_port;
                        @defaultonly drop;
                }

                @name("l2_exact_counter")
                counters = direct_counter(CounterType.packets_and_bytes);

        }


        /*
                Exercise 2 TO-DO: Create an action to build an ARP reply.
                The name of this action will be arp_reply.
                This action will receive a MAC address provided by the
                table match. Keep in mind the following things for this
                action

                1. The operation code is the one corresponding to an ARP
                   reply.
                2. The Target Hardware Address will be set to the source
                   MAC address.
                3. The Source Hardware Address will be set to the MAC address
                   provided by the table match (i.e. the parameter of the
                   action).
                4. The Source Protocol Address will be set to the
                   Target Protocol Address contained in the request
                5. The destination address of the Ethernet header will be set
                   to its source address (to create a reply).
                6. The source address of the Ethernet header will be set to
                   the MAC address provided by the table match (i.e. the
                   parameter of the action).
                7. Return the reply to the same port where it came from by
                   setting the egress_spec field of the standard_metadata
                   structure. (Hint: The ingress port is available in the
                   ingress_port field of this structure, and it has been set
                   at the ParserImpl)
        */


        action arp_reply(mac_addr_t request_mac) {
                // Set the operation code to ARP reply
                hdr.arp.oper = ARP_OPER_REPLY;

                // Set the Target Hardware Address to the Source MAC address from the request
                hdr.arp.tha = hdr.arp.sha;

                // Set the Source Hardware Address to the MAC address provided by the table match
                hdr.arp.sha = request_mac;

                // Set the Source Protocol Address to the Target Protocol Address from the request
                hdr.arp.spa = hdr.arp.tpa;

                // Set the Ethernet header's destination address to its source address
                hdr.ethernet.dst_addr = hdr.ethernet.src_addr;

                // Set the Ethernet header's source address to the MAC address provided by the table match
                hdr.ethernet.src_addr = request_mac;

                // Return the reply to the same port where it came from
                standard_metadata.egress_spec = standard_metadata.ingress_port;
        }



        /*
                Exercise 2 TO-DO: Define the arp_exact table. This table
                will be composed of a key to match the Target Protocol Address
                field of the ARP header, in exact way. The actions for this
                table will be the arp_reply, and the drop action. The drop
                action will be the default action
        */


        table arp_exact {
                key = {
                        hdr.arp.tpa: exact; // Match on Target Protocol Address in an exact way
                }
                actions = {
                        arp_reply;  // Action to build and send an ARP reply
                        drop;       // Action to drop the packet
                }
                default_action = drop(); // Set drop as the default action
                //size = 1024;   // Specify the size of the table
        }




        // --- APPLY -----------------------------------------------------------


        apply {

                if (hdr.cpu_out.isValid()) {
                        standard_metadata.egress_spec = hdr.cpu_out.egress_port;
                        hdr.cpu_out.setInvalid();
                        exit;
                }

                //l2_exact_table.apply();

        /*
                Exercise 2 TO-DO: Modify the apply block according to the
                following algorithm:
                1. If the packet contains valid Ethernet and IPv4 headers,
                   then apply the l2_exact_table which will forward packets
                   according the destination MAC address.
                2. Otherwise, if the packet contains an Ethernet frame,
                   apply the arp_exact table in order to reply ARP requests.
                Hint 1: You might want to comment out the non-conditioned
                application of l2_exact_table.
                Hint 2: For Step 2, you need to check the value of the field
                containing the type of content of the frame.

        */
                if (hdr.ethernet.isValid() && hdr.ipv4.isValid()) {
                        l2_exact_table.apply(); // Apply l2_exact_table for IPv4 packets
                } else if (hdr.ethernet.isValid() && hdr.ethernet.ether_type == ETHERTYPE_ARP) {
                        arp_exact.apply(); // Apply arp_exact table for ARP requests
                }

                acl_table.apply();

        }
}


//+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
//++++++++++++++++++++++++++++ EGRESS PROCESSING ++++++++++++++++++++++++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


control EgressPipeImpl (inout parsed_headers_t hdr,
                        inout local_metadata_t local_metadata,
                        inout standard_metadata_t standard_metadata){


        // --- APPLY ---------------------------------------------------

        apply {

                if (standard_metadata.egress_port == CPU_PORT) {
                        hdr.cpu_in.setValid();
                        hdr.cpu_in.ingress_port=standard_metadata.ingress_port;
                        exit;
                }
        }

}


//+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
//++++++++++++++++++++++++++++++++ CHECKSUM +++++++++++++++++++++++++++++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


control ComputeChecksumImpl(inout parsed_headers_t hdr,
                            inout local_metadata_t local_metadata) {
        apply { /* EMPTY */ }
}


//+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
//++++++++++++++++++++++++++++++++ DEPARSER +++++++++++++++++++++++++++++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


control DeparserImpl(packet_out packet, in parsed_headers_t hdr) {
        apply {
                packet.emit(hdr.cpu_in);
                packet.emit(hdr.ethernet);

        /*
                Exercise 1 TO-DO: In order to get a successfull response,
                modify this method to emit a packet containing an ipv4
                header.
        */
                packet.emit(hdr.ipv4);
        /*
                Exercise 2 TO-DO: Include the ARP header in outgoing packets
                where applicable
        */
                packet.emit(hdr.arp);
        }
}


//+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
//+++++++++++++++++++++++++++++++++ SWITCH ++++++++++++++++++++++++++++++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


V1Switch(
        ParserImpl(),
        VerifyChecksumImpl(),
        IngressPipeImpl(),
        EgressPipeImpl(),
        ComputeChecksumImpl(),
        DeparserImpl()
) main;