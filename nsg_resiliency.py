
import boto3
import time
import os

# VPC B

region = 'us-east-1'
instance_type = 'c4.xlarge'
security_group_id = 'sg-0509dc08db7a2036a'

# Instance ID of the primary NSG
instance_id_nsg_A = 'i-0fcf1cf2c675fca1e'

# Primary NSG Uplink Interface ID
uplink_eni_nsg_A = 'eni-01710703a3ed3946e'

# Primary NSG Uplink Interface Private IP
nsg_A_uplink_primary_ip = '20.0.1.10'

# Secondary NSG Uplink Interface ID
uplink_eni_nsg_B = 'eni-053545c285311adc6'

# Secondary NSG Uplink Interface Private IP
nsg_B_uplink_primary_ip = '20.0.1.9'

# Access interface used by both NSGs
access_eni = 'eni-0332859480e07dc17'

# Elastic IP used by both NSGs
elastic_ip = '18.235.97.139'

# Allocation id of the Elastic IP
allocation_id = 'eipalloc-047ab8d1aa21a11d2'

# NSG Snapshot AMI ID
snapshot_ami_id = 'ami-0a29943124c318e2b'

def exit_with_error(error):
    print error
    exit (1)

# Power OFF the instance if state is running
def power_off_instance_A():
    instance = ""
    state = ""
    try:
        ec2 = boto3.resource('ec2')
        instance = ec2.Instance(instance_id_nsg_A)
        if (instance == ''):
            error = "Instnace with instance id '" + instance_id_nsg_A + "' not found."
            exit_with_error(error)
        state = instance.state['Name']
    except Exception as e:
        error = "Exception while fetching instance resource: " + str(e)
        exit_with_error(error) 

    
    if (state != 'stopped'):
        instances = []
        instances.append(instance_id_nsg_A)
        try:
            resource = boto3.client('ec2', region_name=region)
            resource.stop_instances(InstanceIds=instances)
        except Exception as e:
            error = "Cannot stop instance id '" + instance_id_nsg_A + ". Exception: " + str(e)
            exit_with_error(error)

    print ("Instance Power OFF ... [ SUCCESS ]")     
    return


# Detach access interface from NSG A
def detach_access_interface_from_A():
    ec2 = boto3.resource('ec2')
    access_interface = ''

    try:
        access_interface = ec2.NetworkInterface(access_eni)
    except Exception as e:
        error = "Unable to get access interface resource. Exception: " + str(e)
        exit_with_error(error)

    try:
        if (access_interface.status == 'in-use'):
            access_interface.detach(False, True)
    except Exception as e:
        error = "Unable to detach access network interface. Exception: " + str(e)
        exit_with_error(error)

    if (access_interface.status == 'in-use'):
        time.sleep(5)

    print ("Detach Access Interface ... [ SUCCESS ]")
    return


# Disassociate Elastic IP from NSG A uplink interface
def disassociate_elastic_ip_from_A():
    association_id = ''

    ec2 = boto3.client('ec2')

    # Get association id
    try:
        response = ec2.describe_addresses(
        Filters=[
            {
                'Name': 'public-ip',
                'Values': [elastic_ip]
            }])
        association_id = response['Addresses'][0]['AssociationId']
    except Exception as e:
        error = "Unable to get association id for Elastic IP: " + elastic_ip + ". Exception: " + str(e)
        exit_with_error(error)

    # Disassociate address using association id
    try:
        response = ec2.disassociate_address(AssociationId=association_id)
    except Exception as e:
        error = "Unable to disassociate elastic IP: " + elastic_ip + ". Exception: " + str(e)
        exit_with_error(error)

    print ("Disassociate Elastic IP ... [ SUCCESS ]")
    return


# Associate Elastic IP to NSG B uplink interface
def associate_elastic_ip_to_B():
    ec2 = boto3.client('ec2')
    try:
        response = ec2.associate_address(
            AllocationId = allocation_id,
            NetworkInterfaceId = uplink_eni_nsg_B,
            PrivateIpAddress = nsg_B_uplink_primary_ip
        )
    except Exception as e:
        error = "Unable to associate Elastic IP with Interface with private IP: " + nsg_B_uplink_primary_ip + ". Exception: " + str(e)
        exit_with_error(error)

    print ("Associate Elasltic IP to new NSG ... [ SUCCESS ]")
    return


# Create new NSG instance from existing Snapshot AMI
def create_instance_B_from_snapshot():
    response = ''
    ec2 = boto3.client('ec2', region)
    try:
        response = ec2.run_instances(
        BlockDeviceMappings = [
            {
                'DeviceName': '/dev/sda1',
                'Ebs': { 'DeleteOnTermination': True }
            }
        ],
    ImageId = snapshot_ami_id,
    InstanceType = instance_type,
    MinCount = 1,
    MaxCount = 1,
    NetworkInterfaces = [
            {
                'DeviceIndex': 0,
                'NetworkInterfaceId': uplink_eni_nsg_B,
            },
            {
                'DeviceIndex': 1,
                'NetworkInterfaceId': access_eni,
            }
        ],
    )
    except Exception as e:
        error = "Unable to create new instance. Exception: " + str(e)
        exit_with_error(error)

    try:
        new_instance_id = response['Instances'][0]['InstanceId']
        resource = boto3.resource('ec2')
        instance = resource.Instance(new_instance_id)
        tag = instance.create_tags(Tags=[
                {
                    'Key': 'Name',
                    'Value': 'Resilient-NSG'
                }
            ]
        )
    except Exception as e:
        error = "Unable to change instance name. Exception: " + str(e)
        exit_with_error(error)

    print ("New Instance Creation ... [ SUCCESS ]")
    return


# Lambda callback
def lambda_handler(event, context):
    detach_access_interface_from_A()
    power_off_instance_A()
    disassociate_elastic_ip_from_A()
    associate_elastic_ip_to_B()
    create_instance_B_from_snapshot()
    return "Success!"

