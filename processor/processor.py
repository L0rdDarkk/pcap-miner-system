#!/usr/bin/env python3
import os
import time
import json
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_DIR = os.getenv('WATCH_DIR', '/pcaps')
OUTPUT_DIR = os.getenv('OUTPUT_DIR', '/results')
PROCESSED_FILE = '/tmp/processed_pcaps.txt'

print("=" * 50)
print("PCAP PROCESSOR STARTING")
print("=" * 50)
print(f"Watch directory: {WATCH_DIR}")
print(f"Output directory: {OUTPUT_DIR}")
print("=" * 50)

class PCAPHandler(FileSystemEventHandler):
    def __init__(self):
        self.processed = self.load_processed()
        print(f"Loaded {len(self.processed)} previously processed files")
    
    def load_processed(self):
        """Load list of already processed PCAPs"""
        if os.path.exists(PROCESSED_FILE):
            with open(PROCESSED_FILE, 'r') as f:
                return set(f.read().splitlines())
        return set()
    
    def save_processed(self, filename):
        """Save processed PCAP to tracking file"""
        with open(PROCESSED_FILE, 'a') as f:
            f.write(f"{filename}\n")
    
    def on_created(self, event):
        """Handle new file creation"""
        if event.is_directory:
            return
        
        if event.src_path.endswith(('.pcap', '.pcapng')):
            # Wait for file to be fully written
            time.sleep(2)
            self.process_pcap(event.src_path)
    
    def process_pcap(self, pcap_path):
        """Process a PCAP file using pcap-miner"""
        filename = os.path.basename(pcap_path)
        
        if filename in self.processed:
            print(f" Already processed: {filename}")
            return
        
        print(f"\n{'='*50}")
        print(f"Processing new PCAP: {filename}")
        print(f"{'='*50}")
        
        try:
            # Run pcap-miner in the pcap-miner container
            print(f"⚙️  Executing pcap-miner...")
            result = subprocess.run([
                'docker', 'exec', 'pcap-miner',
                'python', '-m', 'PcapMiner',
                f'/pcaps/{filename}'
            ], capture_output=True, text=True, timeout=300)
            
            # Save results
            output_file = os.path.join(OUTPUT_DIR, f"{filename}.json")
            
            analysis_data = {
                'filename': filename,
                'timestamp': time.time(),
                'pcap_miner_output': result.stdout,
                'pcap_miner_stderr': result.stderr,
                'status': 'success' if result.returncode == 0 else 'error',
                'error': result.stderr if result.returncode != 0 else None,
                'exit_code': result.returncode
            }
            
            with open(output_file, 'w') as f:
                json.dump(analysis_data, f, indent=2)
            
            # Mark as processed
            self.processed.add(filename)
            self.save_processed(filename)
            
            if result.returncode == 0:
                print(f" Analysis complete: {output_file}")
                print(f" Output lines: {len(result.stdout.splitlines())}")
            else:
                print(f"Analysis failed with exit code: {result.returncode}")
                print(f"Error: {result.stderr[:200]}")
            
        except subprocess.TimeoutExpired:
            print(f"  Timeout processing {filename}")
        except Exception as e:
            print(f"Error processing {filename}: {e}")
        
        print(f"{'='*50}\n")

def scan_existing_pcaps():
    """Scan and process any existing PCAP files"""
    print("🔎 Scanning for existing PCAP files...")
    handler = PCAPHandler()
    pcap_files = list(Path(WATCH_DIR).glob('*.pcap*'))
    
    print(f"Found {len(pcap_files)} PCAP files")
    
    for pcap_file in pcap_files:
        if pcap_file.name not in handler.processed:
            print(f" Processing existing file: {pcap_file.name}")
            handler.process_pcap(str(pcap_file))

if __name__ == "__main__":
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Process existing files first
    scan_existing_pcaps()
    
    # Start watching for new files
    print("\n👀 Starting file watcher...")
    event_handler = PCAPHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=False)
    observer.start()
    
    print("PCAP Processor is running!")
    print("Waiting for new PCAP files...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n Stopping PCAP processor...")
        observer.stop()
    observer.join()
