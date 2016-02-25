import os
import sys
import json
import re
import copy
from jinja2 import Template

#
# This file contains common functions for generating AWS CloudFormation templates
#


# http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/mappings-section-structure.html
MAPPINGS = {

  # TODO: we should build our own AMIs in all cases
  # amzn-ami-minimal-hvm-2015.03.rc-1.x86_64-s3
  "MinimalAmazonLinuxAMI": {
    "us-east-1": {"instance": "ami-f02e0f98", "ebs": "ami-822e0fea"}
  }
}


def get_file_tokens(file_name, service_fullname=None):
  """ Returns a local file as a series of tokens and CloudFormation variables/functions """
  with open(file_name, "r") as f:
    cnt = f.read()
    if service_fullname:
      rendered = Template(cnt).render(service_fullname=service_fullname)
      tokens = rendered.split("|||")
      tokens = [json.loads(token) if re.match(r"^\{.*\}$", token) else token for token in tokens]
      return tokens
    else:
      return [cnt]


def get_file(*args):
  """ Returns the CloudFormation-compatible content of a local file interpreted as a jinja2 template """
  return {"Fn::Join": [
    "",
    get_file_tokens(*args)
  ]}


def get_launch_configuration(service_name, service_fullname, storage_type, commands=None, packages=None, files=None, services=None):
  """ Returns the LaunchConfiguration section of a CloudFormation template """

  commands = copy.deepcopy(commands or {})
  packages = copy.deepcopy(packages or {})
  files = copy.deepcopy(files or {})
  services = copy.deepcopy(services or {})

  files["/etc/cfn/cfn-hup.conf"] = {
    "content": {"Fn::Join": ["", [
      "[main]\n",
      "stack=", {"Ref": "AWS::StackId"}, "\n",
      "region=", {"Ref": "AWS::Region"}, "\n"
      "interval=1\n"
    ]]},
    "mode": "000400",
    "owner": "root",
    "group": "root"
  }

  files["/etc/cfn/hooks.d/cfn-auto-reloader.conf"] = {
    "content": {"Fn::Join": ["", [
      "[cfn-auto-reloader-hook]\n",
      "triggers=post.update\n",
      "path=Resources.%sLaunchConfiguration.Metadata.AWS::CloudFormation::Init\n" % service_fullname,
      "action=/opt/aws/bin/cfn-init -v ",
      "         --stack ", {"Ref": "AWS::StackName"},
      "         --resource %sLaunchConfiguration " % service_fullname,
      "         --region ", {"Ref": "AWS::Region"}, "\n",
      "runas=root\n"
    ]]}
  }

  services["cfn-hup"] = {
    "enabled": "true",
    "ensureRunning": "true",
    "files": [
      "/etc/cfn/cfn-hup.conf",
      "/etc/cfn/hooks.d/cfn-auto-reloader.conf"
    ]
  }

  # Parse templates to file contents
  for f in files.itervalues():
    if f.get("_template"):
      f["content"] = get_file(f["_template"], service_fullname)
      del f["_template"]

  launchconfiguration = {
    "Type": "AWS::AutoScaling::LaunchConfiguration",
    "Metadata": {
      "AWS::CloudFormation::Init": {
        "config": {
          "commands": commands,
          "packages": packages,
          "files": files,
          "services": {
            "sysvinit": services
          }
        }
      }
    },
    "Properties": {
      "ImageId": {"Fn::FindInMap": ["MinimalAmazonLinuxAMI", {"Ref": "AWS::Region"}, storage_type]},
      "InstanceType": {"Ref": "%sInstanceType" % service_fullname},
      "AssociatePublicIpAddress": "true",  # TODO
      "IamInstanceProfile": {"Ref": "EC2InstanceProfile"},
      "SecurityGroups": [{"Ref": "EC2InternalSecurityGroup"}, {"Ref": "%sSecurityGroup" % service_name}],
      "KeyName": {"Ref": "KeyName"},
      "UserData": {"Fn::Base64": get_file("aws/%s/ec2-bootstrap.sh" % service_name.lower(), service_fullname)}
    }
  }

  # TODO: add other groups for spot instances
  # if service_fullname == "ElasticsearchData":
  #   launchconfiguration["Properties"]["SpotPrice"] = {"Ref": "ElasticsearchDataSpotBid"}

  return launchconfiguration


def get_auto_scaling_group(service_name, service_fullname):
  """ Returns the AutoScalingGroup section of a CloudFormation template """

  asg = {
    "Type": "AWS::AutoScaling::AutoScalingGroup",
    "Properties": {
      "VPCZoneIdentifier": {"Ref": "SubnetID"},
      "LaunchConfigurationName": {"Ref": "%sLaunchConfiguration" % service_fullname},
      "MinSize": {"Ref": "%sMinSize" % service_fullname},
      "MaxSize": {"Ref": "%sMaxSize" % service_fullname},
      "Cooldown": "60",
      "DesiredCapacity": {"Ref": "%sMinSize" % service_fullname},
      "Tags": [
        {"Key": "Name", "Value": service_fullname, "PropagateAtLaunch": "true"},
        {"Key": "service_name", "Value": service_name.lower(), "PropagateAtLaunch": "true"},
        {"Key": "service_fullname", "Value": service_fullname.lower(), "PropagateAtLaunch": "true"}
      ]
    },
    "CreationPolicy": {
      "ResourceSignal": {
        "Timeout": "PT15M"
      }
    },
    "UpdatePolicy": {
      "AutoScalingRollingUpdate": {
        "MinInstancesInService": "1",
        "MaxBatchSize": "1",
        "PauseTime": "PT15M",
        "WaitOnResourceSignals": "true"
      }
    }
  }

  if service_fullname == "Frontend":
    asg["Properties"]["LoadBalancerNames"] = [{"Ref": "FrontendLoadBalancer"}]
    # TODO "HealthCheckType": "ELB", ?

  elif service_fullname == "ElasticsearchLb":
    asg["Properties"]["LoadBalancerNames"] = [{"Ref": "ElasticsearchLoadBalancer"}]

  return asg
