import sys
import os
import json
import subprocess
from datetime import datetime, timedelta
from dateutil import tz
from dateutil.parser import *
from urllib.parse import unquote


def daterange(start_date, end_date):
    # generator function to iterate days
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def get_page_from_url(url):
    # when run on Windows, URLs will have escape characters before ampersands, so get rid of them
    url = url.replace('^','')
    idx1 = url.find('page=') + 5
    idx2 = url.find('per_page=') - 1
    return url[idx1:idx2]


def get_date_from_url(url):
    idx1 = url.find('created_ats[gte]=') + 17
    idx2 = idx1 + 10
    return url[idx1:idx2]


def get_cf_response(url):
    if os.name == 'nt':
        # Need to escape the URL ampersands when running on Windows
        url = url.replace('&','^&')
        p = subprocess.run(['cf7.exe', 'curl', url], stdout=subprocess.PIPE, shell=True)
    else:
        p = subprocess.run(['cf', 'curl', url], stdout=subprocess.PIPE)
    if p.returncode == 1:
        print("Can't find the CF CLI executable, is it installed?")
        sys.exit(1)

    data = json.loads(p.stdout.decode('utf-8'))    
    return data


def get_org_space(orgs_spaces, incoming_list=[]):
    if orgs_spaces not in ['organizations','spaces']:
        raise Exception('The value of parameter orgs_spaces must be either organizations or spaces')
        
    data = get_cf_response(f'/v3/{orgs_spaces}?order_by=name&per_page=5000')
    print("Incoming List")
    print(incoming_list)
    print('\n')
    
    guids = []
    for g in data['resources']:
        # get a list of guids we already have
        if incoming_list:
            for d in incoming_list:
                if d['guid'] not in guids:
                    guids.append(d['guid'])
        # guids = [i for sublist in [[k for k in d.keys()] for d in incoming_list] for i in sublist]  
        print("guids")
        print(guids)  
        print('\n')      

        # if current guid is not already in the list, add it
        if g['guid'] not in guids:
            incoming_list.append({"guid": g['guid'], "name": g['name']})
        
    print(incoming_list)
    return incoming_list


def get_paginated_events(url):
    all_data = []
    next_page = True
    date = get_date_from_url(url)
    
    while next_page:
        print(f'Working on page {get_page_from_url(url)} of {date} using {url}')
        
        data = get_cf_response(url)
        for resource in data['resources']:
            all_data.append(resource)

        try:
            # if this element exists, a subsequent page exists so get the new URL and continue iteration
            url = unquote(data['pagination']['next']['href'])
            url = url.replace('https://api.fr.cloud.gov','')
        except:
            # break out of loop because this was the last page
            next_page = False
    
    if all_data:        
        return all_data
    else:
        return None


def main(org_name):
    if not os.path.isdir('data'):
        os.makedirs('data')
    if not os.path.isdir(f'data/{org_name}'):
        os.makedirs(f'data/{org_name}')
    if not os.path.isdir(f'data/{org_name}/events'):
        os.makedirs(f'data/{org_name}/events')

    status_file = f'data/{org_name}/status_data.json'

    # get the date and time of last successful audit download
    try:
        with open(status_file) as f:
            data = json.load(f)
    except FileNotFoundError:
        # create the file if it doesn't exist using yesterday's date
        yesterday_time_dt = datetime.utcnow() - timedelta(days=1)
        yesterday_time_str = yesterday_time_dt.isoformat() + 'Z'
        yesterday_date_str = yesterday_time_str[:10]
        data = {}
        data['last_date_of_events_extracted'] = yesterday_date_str
        data['last_date_time_events_extracted'] = yesterday_time_str
        with open(status_file, 'w') as f:
            json.dump(data, f, indent=4)
    
    last_date = data['last_date_of_events_extracted']
    last_time = data['last_date_time_events_extracted']
    # convert to datetime objects
    last_date_dt = parse(last_date)
    last_time_dt = parse(last_time)
    # find the UTC offset of the last download timestamp so we can output with same later
    utc_offset = last_time_dt.utcoffset()
    # get current time using UTC offset 
    if utc_offset:
        curr_time_dt = datetime.now(tz.tzoffset(None, utc_offset))
    else:
        curr_time_dt = datetime.utcnow()
    # convert current time strings holding time and date
    curr_time_str = curr_time_dt.isoformat().replace('+00:00','Z')
    if '+' not in curr_time_str and 'Z' not in curr_time_str:
        curr_time_str = curr_time_str + 'Z'
    curr_date_str = curr_time_str[:10]
    # convert date string to datetime
    curr_date_dt = datetime.strptime(curr_date_str, '%Y-%m-%d')

    # iterate through all dates between the last download date and today
    for d in daterange(last_date_dt, curr_date_dt):
        url = '/v3/audit_events?'
        # build a "from time" string to use as the "greater than or equal to" parameter
        from_time_str = d.strftime('%Y-%m-%d') + 'T00:00:00Z'
        from_day_str = from_time_str[:10]
        # "to time" will be "less than" (not "less than or equal to") so get the next day's date
        to_time = d + timedelta(days=1)
        to_time_str = to_time.strftime('%Y-%m-%d') + 'T00:00:00Z'
        # build the URL for page 1 of pagination
        url = url + 'created_ats[gte]=' + from_time_str
        url = url + '&created_ats[lt]=' + to_time_str 
        url = url + '&page=1&per_page=5000'

        # paginate through all data for this day and store in a list
        day_data = get_paginated_events(url)

        # get log file name and path
        file_name = from_time_str[:7] + '.json'
        file_path = f'data/{org_name}/events/{file_name}'

        # write to file           
        file_dict = {}       
        try:
            # if this month's log file already exists, get the existing data so we can append and overwrite
            with open(file_path, 'r') as f:
                file_dict = json.load(f)
        except FileNotFoundError:
            # if we are creating a new log file, create empty lists for each JSON element
            file_dict['org'] = []
            file_dict['space'] = []
            file_dict['resources'] = []

        # append any new orgs without overwriting existing orgs
        file_dict['org'] = get_org_space('organizations', file_dict['org'])
        # append any new spaces without overwriting existing spaces
        file_dict['space'] = get_org_space('spaces', file_dict['space'])
        # append the new event data to the existing event data
        if day_data:
            for item in day_data:
                file_dict['resources'].append(item)
        # write to file (overwrite existing file if it exists)
        with open(file_path, 'w') as f:
            json.dump(file_dict, f, indent=4)

    # replace the last download date and times in the status json and write to status file 
    data['last_date_of_events_extracted'] = curr_date_str
    data['last_date_time_events_extracted'] = curr_time_str
    with open(status_file, 'w') as f:
        json.dump(data, f, indent=4)
    
    

if __name__ == "__main__":
    # org_name = 'epa-surface-water'
    try:
        org_name = sys.argv[1]
    except IndexError as e:
        print(f'Pass the organization name as a command line argument: {e}')
        sys.exit(1)
    main(org_name)








