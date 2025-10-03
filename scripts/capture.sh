#!/bin/bash

# Packet capture script for Docker containers
PCAP_DIR="/pcaps"
ROTATE_INTERVAL=300  # 5 minutes (300 seconds)
MAX_PACKET_SIZE=65535

mkdir -p "$PCAP_DIR"

echo "========================================="
echo "Starting PCAP Capture System"
echo "========================================="
echo "PCAP directory: $PCAP_DIR"
echo "Rotation interval: ${ROTATE_INTERVAL} seconds"
echo "Max packet size: $MAX_PACKET_SIZE bytes"
echo "========================================="

# Capture on all interfaces, rotate files every 5 minutes
# Excludes SSH traffic to avoid capturing management connections
tcpdump -i any \
    -s $MAX_PACKET_SIZE \
    -G $ROTATE_INTERVAL \
    -w "${PCAP_DIR}/capture_%Y%m%d_%H%M%S.pcap" \
    -Z root \
    'not port 22'

# Alternative filters you can use:
# Capture only HTTP/HTTPS: 'port 80 or port 443'
# Capture only specific subnet: 'net 172.17.0.0/16'
# Exclude specific host: 'not host 10.0.0.1'
