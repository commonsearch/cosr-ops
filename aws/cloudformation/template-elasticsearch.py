#!/usr/bin/env python

#
# This script outputs a CloudFormation template for a Common Search Elasticsearch stack.
#

import sys
import json
import copy
import json
import urlparse
import os

from common import MAPPINGS, get_auto_scaling_group, get_launch_configuration

# Try to read the actual elasticsearch user/password from the config if present.
if not os.path.isfile("configs/cosr-back.prod.json"):
  CONFIG = {
    "ELASTICSEARCHTEXT": "http://admin:admin@127.0.0.1:9200",
    "ELASTICSEARCHTEXT_READONLY": "http://user:user@127.0.0.1:9200",
  }
else:
  with open("configs/cosr-back.prod.json") as f:
    CONFIG = json.load(f)

ELASTICSEARCH_ADMIN_URL = urlparse.urlparse(CONFIG["ELASTICSEARCHTEXT"])
ELASTICSEARCH_READONLY_URL = urlparse.urlparse(CONFIG["ELASTICSEARCHTEXT_READONLY"])

ES_MAPPINGS = copy.deepcopy(MAPPINGS)

ES_MAPPINGS.update({

  # https://aws.amazon.com/ec2/instance-types/
  "InstanceTypes": {

    # ES Heap should be ~50% of available RAM
    "c3.large": {"EsPathData": "/mnt,/mnt2", "EsHeapSize": "1800m"},
    "c3.xlarge": {"EsPathData": "/mnt,/mnt2", "EsHeapSize": "3600m"},
    "c3.2xlarge": {"EsPathData": "/mnt,/mnt2", "EsHeapSize": "8g"},

    "d2.xlarge": {"EsPathData": "/mnt,/mnt2,/mnt3", "EsHeapSize": "16g"},
    "d2.2xlarge": {"EsPathData": "/mnt,/mnt2,/mnt3,/mnt4,/mnt5,/mnt6", "EsHeapSize": "32g"},

    "t2.micro": {"EsPathData": "", "EsHeapSize": "512m"},

    # TODO: these 2 instance types must format their SSDs first
    # http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ssd-instance-store.html
    "r3.large": {"EsPathData": "/mnt", "EsHeapSize": "8g"},
    "r3.xlarge": {"EsPathData": "/mnt", "EsHeapSize": "16g"},
    "i2.xlarge": {"EsPathData": "/mnt", "EsHeapSize": "16g"},
    "i2.2xlarge": {"EsPathData": "/mnt,/mnt2", "EsHeapSize": "32g"},

  }

})

PARAMETERS = {

  "Vpc": {
    "Type": "AWS::EC2::VPC::Id",
    "Default": "vpc-8d46a8e9",
    "Description": "The VPC to place all resources into"
  },

  "KeyName": {
    "Type": "AWS::EC2::KeyPair::KeyName",
    "Default": "local-ssh",
    "Description": "Name of an existing EC2 KeyPair to enable SSH access to the EC2 instances"
  },

  "SubnetID": {
    "Type": "List<AWS::EC2::Subnet::Id>",
    "Default": "subnet-a6354d8d",
    "Description": "List of an existing subnet IDs to use for the load balancer and auto scaling group"
  },



  "ElasticsearchClusterName": {
    "Type": "String",
    "Default": "cosr-es-cluster",
    "Description": "The name of the Elasticsearch cluster"
  },

  "ElasticsearchDataInstanceType": {
    "Description": "The EC2 instance type for Data Elasticsearch nodes",
    "Type": "String",
    "Default": "c3.xlarge",
    "ConstraintDescription": "must be a valid EC2 instance type."
  },
  "ElasticsearchDataMinSize": {
    "Type": "Number",
    "Default": "1",
    "Description": "Minimum number of Data Elasticsearch instances that can be launched"
  },
  "ElasticsearchDataMaxSize": {
    "Type": "Number",
    "Default": "20",
    "Description": "Maximum number of Data Elasticsearch instances that can be launched"
  },
  "ElasticsearchDataSpotBid": {
    "Type": "Number",
    "Default": "0.21",
    "Description": "Dollar to bid on Data spot instances"
  },


  "ElasticsearchLbInstanceType": {
    "Description": "The EC2 instance type for LoadBalancer Elasticsearch nodes",
    "Type": "String",
    "Default": "c3.large",
    "ConstraintDescription": "must be a valid EC2 instance type."
  },
  "ElasticsearchLbMinSize": {
    "Type": "Number",
    "Default": "1",
    "Description": "Minimum number of LoadBalancer Elasticsearch instances that can be launched"
  },
  "ElasticsearchLbMaxSize": {
    "Type": "Number",
    "Default": "20",
    "Description": "Maximum number of LoadBalancer Elasticsearch instances that can be launched"
  },


  "ElasticsearchMasterInstanceType": {
    "Description": "The EC2 instance type for Master Elasticsearch nodes",
    "Type": "String",
    "Default": "t2.micro",
    "ConstraintDescription": "must be a valid EC2 instance type."
  },
  "ElasticsearchMasterMinSize": {
    "Type": "Number",
    "Default": "1",
    "Description": "Minimum number of Master Elasticsearch instances that can be launched"
  },
  "ElasticsearchMasterMaxSize": {
    "Type": "Number",
    "Default": "3",
    "Description": "Maximum number of Master Elasticsearch instances that can be launched"
  }

}


LAUNCHCONFIGURATION = {


  "files": {
    "/etc/elasticsearch/elasticsearch.yml": {
      "_template": "aws/elasticsearch/elasticsearch.yml"
    },
    "/etc/elasticsearch/logging.yml": {
      "_template": "aws/elasticsearch/logging.yml"
    },
    "/etc/elasticsearch/shield/roles.yml": {
      "_template": "aws/elasticsearch/roles.yml"
    },
    "/etc/sysconfig/elasticsearch": {
      "_template": "aws/elasticsearch/sysconfig.sh",
      "mode": "000755"
    }
  },


  "services": {
    "elasticsearch": {
      "enabled": "true",
      "ensureRunning": "true"
    }
  },


  "packages": {
    "yum": {
      "java-1.8.0-openjdk-devel": []
    }
  },


  "commands": {
    # "01_yum_update": {
    #   "command": "yum update -y"
    # },
    "10_install_elasticsearch": {
      "command": "rpm -ivh https://download.elastic.co/elasticsearch/release/org/elasticsearch/distribution/rpm/elasticsearch/2.3.4/elasticsearch-2.3.4.rpm"
    },
    "11_elasticsearch_plugins": {
      "command": (
        "/usr/share/elasticsearch/bin/plugin install cloud-aws && " +
        "/usr/share/elasticsearch/bin/plugin install license && " +
        "/usr/share/elasticsearch/bin/plugin install shield && "
        "/usr/share/elasticsearch/bin/plugin install mobz/elasticsearch-head && " +
        "/usr/share/elasticsearch/bin/plugin install lmenezes/elasticsearch-kopf/2.0 && " +
        "/usr/share/elasticsearch/bin/plugin install AIsaac08/bigdesk"  # TODO switch to main repo when compatible!
      )
    },
    "12_elasticsearch_admin": {
      "command": "/usr/share/elasticsearch/bin/shield/esusers useradd %s -r admin -p %s" % (ELASTICSEARCH_ADMIN_URL.username, ELASTICSEARCH_ADMIN_URL.password)
    },
    "13_elasticsearch_user": {
      "command": "/usr/share/elasticsearch/bin/shield/esusers useradd %s -r user -p %s" % (ELASTICSEARCH_READONLY_URL.username, ELASTICSEARCH_READONLY_URL.password)
    }
  }
}


RESOURCES = {

  "ElbSecurityGroup": {
    "Type": "AWS::EC2::SecurityGroup",
    "Properties": {
      "GroupDescription": "Ports that the public can access on our ELB",
      "VpcId": {"Ref": "Vpc"},
      "SecurityGroupIngress": [
        {"IpProtocol": "tcp", "FromPort": 9200, "ToPort": 9200,
         "CidrIp": "0.0.0.0/0"},
        {"IpProtocol": "tcp", "FromPort": 9300, "ToPort": 9300,
         "CidrIp": "0.0.0.0/0"},
        {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22,
         "CidrIp": "0.0.0.0/0"}
      ]
    }
  },

  "EC2InternalSecurityGroup": {
   "Type": "AWS::EC2::SecurityGroup",
   "Properties": {
     "GroupDescription": "Ports that our ELB can access of our EC2 cluster.",
     "VpcId": {"Ref": "Vpc"},
     "SecurityGroupIngress": [
       {
         "IpProtocol": "tcp",
         "FromPort": 1,
         "ToPort": 65535,
         "SourceSecurityGroupId": {"Ref": "ElbSecurityGroup"}
       }, {
         "IpProtocol": "tcp",
         "FromPort": 1,
         "ToPort": 65535,
         "CidrIp": "0.0.0.0/0"
       }
     ]
    }
  },

  "ElasticsearchSecurityGroup": {
    "Type": "AWS::EC2::SecurityGroup",
    "Properties": {
      "GroupDescription": "Group for ES to perform self discovery within.",
      "VpcId": {"Ref": "Vpc"}
    }
  },

  "EC2Role": {
    "Type": "AWS::IAM::Role",
    "Properties": {
      "AssumeRolePolicyDocument": {
        "Statement": [
          {
            "Effect": "Allow",
            "Principal": {
              "Service": [
                "ec2.amazonaws.com"
              ]
            },
            "Action": [
              "sts:AssumeRole"
            ]
          }
        ]
      }
    }
  },

  "EC2InstanceProfile": {
    "Type": "AWS::IAM::InstanceProfile",
    "Properties": {
      "Path": "/",
      "Roles": [
        {
          "Ref": "EC2Role"
        }
      ]
    }
  },

  # This user is allowed to list the EC2 instances, used for Elasticsearch discovery
  "InternalUser": {
    "Type": "AWS::IAM::User",
    "Properties": {
      "Path": "/",
      "Policies": [{
        "PolicyName": "root",
        "PolicyDocument": {
            "Statement": [
                {
                    "Action": [
                        "ec2:DescribeInstances"
                    ],
                    "Effect": "Allow",
                    "Resource": [
                        "*"
                    ]
                }
            ],
            "Version": "2012-10-17"
        }
      }]
    }
  },

  "InternalUserKeys": {
    "Type": "AWS::IAM::AccessKey",
    "Properties": {
      "UserName": {"Ref": "InternalUser"}
    }
  },

  "ElasticsearchLoadBalancer": {
    "Type": "AWS::ElasticLoadBalancing::LoadBalancer",
    "Properties": {
      "Subnets": {"Ref": "SubnetID"},
      "SecurityGroups": [{"Ref": "ElbSecurityGroup"}],
      "CrossZone": "true",
      "Scheme": "internet-facing",  # internal",
      "Listeners": [{
        "Protocol": "HTTP",
        "InstanceProtocol": "HTTP",
        "LoadBalancerPort": 9200,
        "InstancePort": 9200
      }, {
        "Protocol": "HTTP",
        "InstanceProtocol": "HTTP",
        "LoadBalancerPort": 9300,
        "InstancePort": 9300
      }],
      "HealthCheck": {
        "Target": "HTTP:9200/",
        "HealthyThreshold": "2",
        "UnhealthyThreshold": "10",
        "Interval": "30",
        "Timeout": "5"
      }
    }
  },

  "ElasticsearchDataLaunchConfiguration": get_launch_configuration("Elasticsearch", "ElasticsearchData", "instance", **LAUNCHCONFIGURATION),
  "ElasticsearchMasterLaunchConfiguration": get_launch_configuration("Elasticsearch", "ElasticsearchMaster", "ebs", **LAUNCHCONFIGURATION),
  "ElasticsearchLbLaunchConfiguration": get_launch_configuration("Elasticsearch", "ElasticsearchLb", "ebs", **LAUNCHCONFIGURATION),

  "ElasticsearchDataAutoScalingGroup": get_auto_scaling_group("Elasticsearch", "ElasticsearchData"),
  "ElasticsearchMasterAutoScalingGroup": get_auto_scaling_group("Elasticsearch", "ElasticsearchMaster"),
  "ElasticsearchLbAutoScalingGroup": get_auto_scaling_group("Elasticsearch", "ElasticsearchLb")


}

TEMPLATE = {
  "AWSTemplateFormatVersion": "2010-09-09",
  "Description": "Common Search Elasticsearch stack",

  "Parameters": PARAMETERS,

  "Mappings": ES_MAPPINGS,

  "Resources": RESOURCES,

  "Outputs": {
    "ElasticsearchLoadBalancerDNSName": {
      "Description": "The DNSName of the Elasticsearch load balancer",
      "Value": {"Fn::GetAtt": ["ElasticsearchLoadBalancer", "DNSName"]}
    }

  }
}

print json.dumps(TEMPLATE, indent=(4 if "--pretty" in sys.argv else None))
