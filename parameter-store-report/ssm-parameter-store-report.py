import os
import boto3
from collections import defaultdict
import xlsxwriter

# Read from env region to query ssm parameters
REGION = os.getenv('REGION')

parameters = defaultdict(lambda: defaultdict(lambda: defaultdict(str)))

def get_resources_from_describe_parameter(ssm_details):
    list_parameters = ssm_details['Parameters']
    resources = [parameters for parameters in list_parameters]
    next_token = ssm_details.get('NextToken', None)
    return resources, next_token

def query_ssm_vars_from_region(region):
    try:
        print ("Querying SSM variables in region {}".format(region))
        session = boto3.Session()
        ssm = session.client('ssm', region_name=region)
        next_token = ' '
        ssm_variables = []
        while next_token is not None:
            ssm_details = ssm.describe_parameters(MaxResults=50, NextToken=next_token)
            current_batch, next_token = get_resources_from_describe_parameter(ssm_details)
            ssm_variables += current_batch
    except Exception as e:
        print ("Error: {}".format(e))

    # Loop for each ssm parameter in staging region 
    for ssm_variable in ssm_variables:
        try:
            ssm_variable_name = ssm_variable.get("Name")
            path_info = ssm_variable_name.split("/")
            env = path_info[2]
            ms_name = path_info[1]
            ms_variable = path_info[3]
            ssm_value = ssm.get_parameter(Name=ssm_variable_name, WithDecryption=True).get("Parameter").get("Value", "")
            print("Getting " + ssm_variable_name + " ...")
            parameters[ms_name][ms_variable][env] = ssm_value
        except Exception as e:
            print ("Error {0} - querying {1} ".format(e, ssm_variable.get("Name")))

# Query all variables in region
query_ssm_vars_from_region(REGION)

# Writing report
workbook = xlsxwriter.Workbook('output/ssm-parameter-store-report.xlsx')
worksheet = workbook.add_worksheet("Variables")
header_format = workbook.add_format({'bg_color': '#93CCEA'})\

# Writing headers
worksheet.set_column('A:C', 25)
worksheet.write('A1', 'MICROSERVICE', header_format)
worksheet.write('B1', 'VARIABLE', header_format)
worksheet.write('C1', 'DEV', header_format)
worksheet.write('D1', 'PRODUCTION', header_format)
worksheet.freeze_panes(1, 0)

row = 1
ms_keys_order = parameters.keys()
sorted(ms_keys_order)
for ms_key in ms_keys_order:
    var_keys_order = parameters[ms_key].keys()
    sorted(var_keys_order)
    for var_key in var_keys_order:
        worksheet.write(row, 0, ms_key)
        worksheet.write(row, 1, var_key)
        worksheet.write(row, 2, parameters[ms_key][var_key].get("dev", "No available"))
        worksheet.write(row, 3, parameters[ms_key][var_key].get("prod", "No available"))
        row += 1

# Add autofiler
worksheet.autofilter('A1:C{0}'.format(row))
workbook.close()
print('done')
