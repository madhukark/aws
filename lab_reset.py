
import boto3
import pprint
import os

region = 'us-east-1'
instance_type = 'c4.xlarge'
security_group_id = 'sg-0509dc08db7a2036a'


def exit_with_error(error):
    print "ERROR: " + error
    exit (1)

# Get Instance ID from a given Instance Name
# NOTE: Returns the first instance ID in case of multiple instances with
#       the same name
def get_instance_id(instance_name):
    ec2 = boto3.client('ec2')
    response = ec2.describe_instances(
        Filters = [
            {
                'Name': 'tag:Name',
                'Values': [instance_name]
            }
        ]
    )
    try:
        instance_id = response['Reservations'][0]['Instances'][0]['InstanceId']
    except Exception as e:
        error = "Unable to get instance " + instance_name + " ID. Exception: " + str(e)
        exit_with_error(error)

    return instance_id


# Get Interface ID from a given Interface Name
# NOTE: Returns the first interface ID in case of multiple interfaces with
#       the same name
def get_interface_id(interface_name):
    ec2 = boto3.client('ec2')
    response = ec2.describe_network_interfaces(
        Filters = [
            {
                'Name': 'tag:Name',
                'Values': [interface_name]
            }
        ]
    )
    try:
        interface_id = response['NetworkInterfaces'][0]['NetworkInterfaceId']
    except Exception as e:
        error = "Unable to get interface " + interface_name + " ID. Exception: " + str(e)
        exit_with_error(error)

    return interface_id


# Get Interface Private IP from a given Interface Name
# NOTE: Returns the first Private IP
def get_private_ip(interface_name):
    ec2 = boto3.client('ec2')
    response = ec2.describe_network_interfaces(
        Filters = [
            {
                'Name': 'tag:Name',
                'Values': [interface_name]
            }
        ]
    )
    try:
        private_ip = response['NetworkInterfaces'][0]['PrivateIpAddress']
    except Exception as e:
        error = "Unable to get interface " + interface_name + " private IP. Exception: " + str(e)
        exit_with_error(error)

    return private_ip


# Get association ID of an Elastic IP
def get_association(elastic_ip):
    ec2 = boto3.client('ec2')
    try:
        response = ec2.describe_addresses(
            Filters = [
                {
                    'Name': 'public-ip',
                    'Values': [elastic_ip]
                }
            ]
        )
        association_id = response['Addresses'][0]['AssociationId']
    except Exception as e:
        error = "Unable to get association ID for Elastic IP: " + elastic_ip + ". Exception: " + str(e)
        exit_with_error(error)

    return association_id


# Get allocation ID of an Elastic IP
def get_allocation(elastic_ip):
    ec2 = boto3.client('ec2')
    try:
        response = ec2.describe_addresses(
            Filters = [
                {
                    'Name': 'public-ip',
                    'Values': [elastic_ip]
                }
            ]
        )
        allocation_id = response['Addresses'][0]['AllocationId']
    except Exception as e:
        error = "Unable to get allocation ID for Elastic IP: " + elastic_ip + ". Exception: " + str(e)
        exit_with_error(error)

    return allocation_id


# Power OFF instance
def power_off_instance(instance_name):
    instance_id = get_instance_id(instance_name)
    print instance_id
    instance = ""
    state = ""
    try:
        ec2 = boto3.resource('ec2')
        instance = ec2.Instance(instance_id)
        state = instance.state['Name']
    except Exception as e:
        error = "Exception while fetching instance state: " + str(e)
        exit_with_error(error)

    if (state != 'stopped'):
        try:
            ec2 = boto3.client('ec2', region_name = region)
            ec2.stop_instances([instance_id])
        except Exception as e:
            error = "Cannot stop instance " + instance_name + ". Exception: " + str(e)
            exit_with_error(error)

    msg = "Instance " + instance_name + " Power OFF ...[ SUCCESS ]"
    print msg
    return


# Detach an interface. Doesnt matter which Instance its associated with.
# NOTE: Assumes its a secondary interface
def detach_interface_from_instance(interface_name)
    interface_id = get_interface_id(interface_name)
    ec2 = boto3.resource('ec2')
    try:
        access_interface = ec2.NetworkInterface(interface_id)
    except Exception as e:
        error = "Unable to get interface " + interface_name + " with ID " + interface_id + " resource. Exception " + str(e)
        exit_with_error(error)

    try:
        access_interface.detach(False, True) # Dryrun, Force
    except Exception as e:
        error = "Unable to detach interface " + interface_name + " with ID " + interface_id " +. Exception: " + str(e)

    msg = " Detach Network Interface : " + interface_name + " ... [ SUCCESS ]"
    print msg
    return


# Disassociate an Elastic IP from an instance/interface
def disassociate_elastic_IP(elastic_ip):
    association_id = get_association_id(elastic_ip)

    ec2 = boto3.client('ec2')
    try:
        response = ec2.disassociate_address(AllocationId=allocation_id)
    except Exception as e:
        error = "Unable to disassociate elastic IP " + elastic_ip + ". Exception: " + str(e)
        exit_with_error(error)

    msg = "Disassociate Elastic IP " + elastic_ip + " ... [ SUCCESS ]"
    print msg
    return


# Associate an Elastic IP to an Instance/Interface
def associate_elastic_IP(elastic_ip, interface_name):
    allocation_id = get_allocation_id(elastic_ip)
    interface_id = get_interface_id(interface_name)
    private_ip_address = get_private_ip(interface_name)

    ec2 = boto3.client('ec2')
    try:
        response = ec2.associate_address(
            AllocationId = allocation_id,
            NetworkInterfaceId = interface_id,
            PrivateIpAddress = private_ip
        )
    except Exception as e:
        error = "Unable to associate elastic IP " + elastic_ip + " with interface " + interface_name + ". Exception: " + str(e)
        exit_with_error(error)
   
    msg = "Associate Elastic IP " + elastic_ip + " to Interface " + interface_name + " ... [ SUCCESS ]"
    print msg 
    return


# Attach interface to an instance
def attach_interface_to_instance(interface_name, instance_name):
    interface_id = get_interface_id(interface_name)
    instance_id = get_instance_id(instance_name)

    ec2 = boto3.resource('ec2')
    network_interface = ec2.NetworkInterface(interface_id)
    try:
        response = network_interface.attach(
            DeviceIndex = 1, # We know its not primary
            DryRun = False,
            InstanceId = instance_id
        )
    except Exception as e:
        error = "Unable to attach interface " + interface_name + " to instance " + instance_name + ". Exception: " + str(e)
        exit_with_error(error)

    msg = "Attach Interface " + interface_name + " to Instance " + instance_name + " ... [ SUCCESS ]"
    print msg
    return


# Power ON instance
def power_on_instance(instance_name):
    instance_id = get_instance_id(instance_name)

    try:
        ec2 = boto3.resource('ec2')
        instance = ec2.Instance(instance_id)
        state = instance.state['Name']
    except Exception as e:
        error = "Exception while fetching instance state: " + str(e)
        exit_with_error(error)

    if (state != 'running'):
        try:
            ec2 = boto3.client('ec2', region_name = region)
            ec2.start_instances([instance_id])
        except Exception as e:
            error = "Cannot start instance " + instance_name + ". Exception: " + str(e)
            exit_with_error(error)    

    msg = "Power ON of instance " + instance_name + " ... [ SUCCESS ]"
    print msg
    return


# Lambda callback
def lambda_handler(event, context):
    power_off_instance('nsg-A')
#    detach_access_interface(access_eni, instance)
#    disassociate_elastic_ip(elastic_ip)
#    associate_elastic_ip(elastic_ip, uplink_eni_nsg_A)
#    attach_access_interface(access_eni, instance)
    return "Success!"
