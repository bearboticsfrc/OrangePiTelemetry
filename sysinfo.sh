#!/bin/bash

export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

HIDE_IP_PATTERN="^dummy0|^lo"
# Temperature offset in Celcius degrees
CPU_TEMP_OFFSET=0

function getboardtemp() {
	if [ -f /etc/orangepimonitor/datasources/soctemp ]; then
		read raw_temp </etc/orangepimonitor/datasources/soctemp 2>/dev/null
		if [ ! -z $(echo "$raw_temp" | grep -o "^[1-9][0-9]*\.\?[0-9]*$") ] && (( $(echo "${raw_temp} < 200" |bc -l) )); then
			# Allwinner legacy kernels output degree C
			board_temp=${raw_temp}
		else
			board_temp=$(awk '{printf("%d",$1/1000)}' <<<${raw_temp})
		fi
	elif [ -f /etc/orangepimonitor/datasources/pmictemp ]; then
		# fallback to PMIC temperature
		board_temp=$(awk '{printf("%d",$1/1000)}' </etc/orangepimonitor/datasources/pmictemp)
	fi
	# Some boards, such as the Orange Pi Zero LTS, report shifted CPU temperatures
	board_temp=$((board_temp + CPU_TEMP_OFFSET))
} # getboardtemp



function get_ip_addresses() {
	local ips=()
	for f in /sys/class/net/*; do
		local intf=$(basename $f)
		# match only interface names "dummy0" and "lo"
		if [[ $intf =~ $HIDE_IP_PATTERN ]]; then
			continue
		else
			local tmp=$(ip -4 addr show dev $intf | grep -v "$intf:avahi" | awk '/inet/ {print $2}' | cut -d'/' -f1)
			# add both name and IP - can be informative but becomes ugly with long persistent/predictable device names
			#[[ -n $tmp ]] && ips+=("$intf: $tmp")
			# add IP only
			[[ -n $tmp ]] && ips+=("$tmp")
		fi
	done
	echo "${ips[*]}" | tr '\n' ' '
} # get_ip_addresses


# query various systems and send some stuff to the background for overall faster execution.
# Works only with ambienttemp and batteryinfo since A20 is slow enough :)
ip_address=$(get_ip_addresses &)
getboardtemp

# get uptime, logged in users and load in one take
UPTIME=$(LC_ALL=C uptime)
UPT1=${UPTIME#*'up '}
UPT2=${UPT1%'user'*}
time=${UPT2%','*}
time=${time//','}
time=$(echo $time | xargs)
load=${UPTIME#*'load average: '}
load=${load//','}
load=$(echo $load | cut -d" " -f1)
[[ $load == 0.0* ]] && load=0.10
cpucount=$(grep -c processor /proc/cpuinfo)

load=$(awk '{printf("%.0f",($1/$2) * 100)}' <<< "$load $cpucount")

# memory 
mem_info=$(LC_ALL=C free -w 2>/dev/null | grep "^Mem" || LC_ALL=C free | grep "^Mem")
memory_usage=$(awk '{printf("%.0f",(($2-($4+$6+$7))/$2) * 100)}' <<<${mem_info})

#####################################################################################3333
# display info
printf "{\n"
printf "\"SystemLoad\": $load,\n"
printf "\"UpTime\": \"$time\",\n" 
printf "\"MemoryUsage\": $memory_usage,\n"
printf "\"IP\": \"$ip_address\",\n"
printf "\"CPUtemp\": $board_temp\n"
printf "}\n"



