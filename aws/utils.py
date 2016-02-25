import re
import os
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
    os.system("ssh %s %s@%s '%s'" % (
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