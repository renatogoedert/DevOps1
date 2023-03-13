#!/usr/bin/bash
# Some basic monitoring functionality; Tested on Amazon Linux 2
#

INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
INSTANCE_TYPE=$(curl -s http://169.254.169.254/latest/meta-data/instance-type)
INSTANCE_KEY=$(curl -s http://169.254.169.254/latest/meta-data/public-keys/0/)
MEMORYUSAGE=$(free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2 }')
CPUUSAGE=$(top -n 1 -b | awk '/^%Cpu/{printf "%.2f%%", $2}')
DISKUSAGE=$(df -h | awk '{sum += $5} END {printf "%.2f%%", sum}')
PROCESSES=$(expr $(ps -A | grep -c .) - 1)
HTTPD_PROCESSES=$(ps -A | grep -c httpd)
NETCONNECTIONS=$(expr $(netstat | grep -c .) - 1)

echo "Instance ID: $INSTANCE_ID"
echo "Instance Type: $INSTANCE_TYPE"
echo "Format Key: $INSTANCE_KEY"
echo "Memory utilisation: $MEMORYUSAGE"
echo "CPU utilisation: $CPUUSAGE"
echo "Disk utilisation: $DISKUSAGE"
echo "No of processes: $PROCESSES"
echo "No of connections: $NETCONNECTIONS"
if [ $HTTPD_PROCESSES -ge 1 ]
then
    echo "Web server is running"
else
    echo "Web server is NOT running"
fi
