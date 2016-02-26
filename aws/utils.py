import re
import os
import subprocess
import time
from jinja2 import Template
from boto import ec2

from .config import CONFIG


SSH_ARGS = '-i configs/%s.pem -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null' % CONFIG["AWS_KEYNAME"]
AWS_USER = CONFIG["AWS_USER"]


def get_command_from_template(command_template):
    """ Returns a command from a Jinja2 template, with config as variables """
    return re.sub("\s+", " ", Template(command_template).render(CONFIG)).strip()


def ssh(instance, command):
    """ Executes a SSH command on a remote instance """
    os.system("ssh -t %s %s@%s '%s'" % (
        SSH_ARGS, AWS_USER, instance.public_dns_name, command
    ))


def send_cosrback_source(instance):
    """ Sends the current source of cosr-back to the instance and uncompress it in the /cosr/back dir """

    # TODO: pull directly from GitHub with a commit hash?

    os.system("cd ../cosr-back/ && make build_source_export")
    os.system("scp %s ../cosr-back/build/source_export.tgz %s@%s:/cosr/back_source_export.tgz" % (
      SSH_ARGS, AWS_USER, instance.public_dns_name
    ))

    ssh(instance,
        'rm -rf /cosr/back/* && cd /cosr/back/ && tar -zxvf ../back_source_export.tgz ' +
        '&& make virtualenv && ldconfig /usr/local/lib'
        )

    # copy config
    os.system("scp %s configs/cosr-back.prod.json %s@%s:/cosr/back/cosr-config.json" % (
        SSH_ARGS, AWS_USER, instance.public_dns_name
    ))


def import_cosrback_local_data(instance):
    """ Imports the local-data from cosr-back on the instance """

    ssh(instance,
        'cd /cosr/back/ && source venv/bin/activate && make import_local_data'
        )

def is_ssh_available(host, user=AWS_USER):
    """ Checks if SSH is available on a host. """

    s = subprocess.Popen(
        ['ssh'] + SSH_ARGS.split(" ") + ['-t', '-t', '-o', 'ConnectTimeout=3', '%s@%s' % (user, host), "true"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    cmd_output = s.communicate()[0]  # [1] is stderr

    return s.returncode == 0

def create_ec2_instance(name, instance_type="t2.micro", ami=CONFIG["AWS_SPARK_AMI"]):
    """ Creates an instance on EC2 with our default configuration """

    conn = ec2.connect_to_region(CONFIG["AWS_REGION"])
    reservation = conn.run_instances(
        ami,
        key_name=CONFIG["AWS_KEYNAME"],
        instance_type=instance_type,
        security_group_ids=[CONFIG["AWS_SECURITYGROUP"]],
        subnet_id=CONFIG["AWS_SUBNET"]
    )
    time.sleep(15)
    instance = reservation.instances[0]
    status = instance.update()

    while status == 'pending':
        time.sleep(10)
        status = instance.update()

    if status == 'running':
        instance.add_tag("Name", name)
    else:
        raise "Unknown instance status:", status

    while not is_ssh_available(instance.public_dns_name):
        time.sleep(5)

    return instance


def lookup_ec2_instances(name_prefix=""):
    """ Returns a list of all matching EC2 instances """

    conn = ec2.connect_to_region(CONFIG["AWS_REGION"])
    res = conn.get_all_instances(filters={
        "tag:Name": "%s*" % name_prefix,
        "instance-state-name": "running"
    })
    return list(res)


def resize_root_volume(instance):
    """ Grows the root volume & partition from 8gb to the actual EBS size. """

    # TODO: could we avoid this by fixing our Packer image?

    # See https://www.elastic.co/blog/autoresize-ebs-root-volume-on-aws-amis
    ssh(instance,
        'yum update -y && ' +
        'yum-config-manager --enable epel && ' +
        'yum install -y cloud-utils-growpart && ' +
        '/usr/bin/growpart /dev/xvda 1 && ' +
        'resize2fs /dev/xvda1'
        )