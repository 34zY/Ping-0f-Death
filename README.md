# Ping-0f-Death
HEAVILY multi-threaded DOS/DDOS ping tool with GUI interface

## Demo (Command line & Graphical Interface)

![PoC](https://github.com/34zY/Ping-0f-Death/blob/main/demo/GUI.gif)

## Features

- Multi-threaded ICMP flood attack
- Verbose mode to track packets sent
- Monitoring mode to check target response
- Graphical User Interface (GUI) for easy use
- Enhanced security and input validation
- Real-time activity logging
- Support for single target or multiple targets from file
- Cross-platform (Linux/Windows)

## Installation

```shell
git clone https://github.com/34zY/Ping-0f-Death.git
cd Ping-0f-Death/
```

## Usage (Graphical interface)
```shell
python PoD_GUI.py
```

GUI Features:

- No command line knowledge required
- Real-time activity log with color coding
- Easy target selection (single IP or file)
- Thread count configuration
- Verbose and monitor mode toggles
- Start/Stop/Clear controls
- Status bar with active thread counter


## Usage (Command line)
```shell
# Single target
python PoD.py -i <Target IP> -t <Threads> [-v] [-m]
# Multiple targets
python PoD.py -l targets.txt -t <Threads> [-v] [-m]

# Examples
python PoD.py -i 192.168.1.1 -t 100 -v -m
python PoD.py -l targets.txt -t 50 -m
```

Options:

- -i <IP> : Single target IP address
- -l <file> : File containing list of IPs (one per line)
- -t <threads> : Number of threads per target (max 5000)
- -v : Verbose mode (show packets sent count)
- -m : Monitor mode (check target response every 10s)
- -h : Show help message

## Disclaimer
I'm not responsible for bad uses of this script.

## Author
@34zY
