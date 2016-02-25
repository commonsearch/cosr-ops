#!/bin/bash -xe

yum install -y aws-cfn-bootstrap mdadm

useradd -d /home/elasticsearch -M -U -s /sbin/nologin -c "elasticsearch user" elasticsearch

# Only setup a data dir for ElasticsearchData instances
{% if service_fullname == "ElasticsearchData" %}

# TODO: factorize all of this a bit better!

# Comment the existing lines in fstab for our local volumes
sed -i '/[/]xvdb/ s/^/#/' /etc/fstab
sed -i '/[/]xvdc/ s/^/#/' /etc/fstab
sed -i '/[/]xvdd/ s/^/#/' /etc/fstab
sed -i '/[/]xvde/ s/^/#/' /etc/fstab
sed -i '/[/]xvdf/ s/^/#/' /etc/fstab
sed -i '/[/]xvdg/ s/^/#/' /etc/fstab

/bin/echo /dev/xvdb   /mnt   ext4    defaults,nofail,noatime,nodiratime,norelatime,discard   0   2 >> /etc/fstab
/bin/echo /dev/xvdc   /mnt2   ext4    defaults,nofail,noatime,nodiratime,norelatime,discard   0   2 >> /etc/fstab
/bin/echo /dev/xvdd   /mnt3   ext4    defaults,nofail,noatime,nodiratime,norelatime,discard   0   2 >> /etc/fstab
/bin/echo /dev/xvde   /mnt4   ext4    defaults,nofail,noatime,nodiratime,norelatime,discard   0   2 >> /etc/fstab
/bin/echo /dev/xvdf   /mnt5   ext4    defaults,nofail,noatime,nodiratime,norelatime,discard   0   2 >> /etc/fstab
/bin/echo /dev/xvdg   /mnt6   ext4    defaults,nofail,noatime,nodiratime,norelatime,discard   0   2 >> /etc/fstab

mkdir -p /mnt /mnt2 /mnt3 /mnt4 /mnt5 /mnt6
umount /dev/xvdb || true
umount /dev/xvdc || true
umount /dev/xvdd || true
umount /dev/xvde || true
umount /dev/xvdf || true
umount /dev/xvdg || true
mount /mnt
mount /mnt2
mount /mnt3
mount /mnt4
mount /mnt5
mount /mnt6
chown -R elasticsearch /mnt*

# This was used to create a RAID0 on d2 instances, but it seems to be recommended to avoid
# RAID with ES setups and JBOD (use the disks directly)
# mdadm --create --verbose /dev/md0 --level=0 --name=esraid --raid-devices=3 /dev/xvdb /dev/xvdc /dev/xvdd
# mkfs.ext4 -L esraid /dev/md0
# mkdir -p /mnt/esraid
# mount LABEL=esraid /mnt/esraid/
# echo "LABEL=esraid  /mnt/esraid ext4  defaults,nofail 0 2" >> /etc/fstab
# chown -R elasticsearch /mnt/esraid/

# TODO? http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/disk-performance.html
# dd if=/dev/zero bs=1M|tee /dev/sdb|tee /dev/sdc|tee /dev/sde > /dev/sdd
# echo $((30*1024)) > /proc/sys/dev/raid/speed_limit_min

{% endif %}

/opt/aws/bin/cfn-init -v --stack |||{"Ref":"AWS::StackName"}|||  --resource {{ service_fullname }}LaunchConfiguration --region |||{"Ref":"AWS::Region"}|||

/opt/aws/bin/cfn-signal -e $? --stack |||{"Ref":"AWS::StackName"}|||  --resource {{ service_fullname }}AutoScalingGroup --region |||{"Ref":"AWS::Region"}|||
