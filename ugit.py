import os
import urequests
import json
import machine
import time
import network
import ntptime
from machine import Pin
from secrets import ssid, password, github_user, github_repo, github_token

default_branch = 'master'
ignore_files = ['ugit.py', 'secrets.py', '.DS_Store']
ignore = ignore_files
giturl = f'https://github.com/{github_user}/{github_repo}'
commit_url = f'https://api.github.com/repos/{github_user}/{github_repo}/commits/{default_branch}'
call_trees_url = f'https://api.github.com/repos/{github_user}/{github_repo}/git/trees/{default_branch}?recursive=1'
raw = f'https://raw.githubusercontent.com/{github_user}/{github_repo}/{default_branch}/'

led = Pin("LED", Pin.OUT)

def get_latest_commit_hash_and_message():
    headers = {'User-Agent': 'ota-pico'}
    if len(github_token) > 0:
        headers['authorization'] = f"bearer {github_token}"
    r = urequests.get(commit_url, headers=headers)
    data = json.loads(r.content.decode('utf-8'))
    return data['sha'], data['commit']['message']

def load_local_commit_hash():
    try:
        with open('ugit_log.txt', 'r') as f:
            content = f.read()
            for line in reversed(content.splitlines()):
                if line.startswith('Update ID: '):
                    return line.split('Update ID: ')[1].strip()
    except:
        pass
    return None

def pull(f_path, raw_url):
    print(f'Pulling {f_path} from GitHub')
    headers = {'User-Agent': 'ota-pico'}
    if len(github_token) > 0:
        headers['authorization'] = f"bearer {github_token}"
    r = urequests.get(raw_url, headers=headers)
    try:
        new_file = open(f_path, 'wb')
        new_file.write(r.content)
        new_file.close()
    except:
        print('Virhe.')

def is_dst(t):
    year, month, day, hour, _, _, _, _ = t
    march_last_sunday = 31 - (time.mktime((year, 3, 31, 0, 0, 0, 0, 0)) % 7)
    oct_last_sunday = 31 - (time.mktime((year, 10, 31, 0, 0, 0, 0, 0)) % 7)
    if month < 3 or month > 10:
        return False
    if month > 3 and month < 10:
        return True
    if month == 3:
        if day < march_last_sunday:
            return False
        if day > march_last_sunday:
            return True
        return hour >= 1
    if month == 10:
        if day < oct_last_sunday:
            return True
        if day > oct_last_sunday:
            return False
        return hour < 1

def get_finland_time():
    utc = time.localtime()
    offset = 3 if is_dst(utc) else 2
    fin_time = time.localtime(time.mktime(utc) + offset * 3600)
    return fin_time

def pull_all(tree=call_trees_url, raw=raw, ignore=ignore, isconnected=False):
    if not isconnected:
        wlan = wificonnect()
        time.sleep(2)
        ntptime.settime()
    latest_hash, commit_message = get_latest_commit_hash_and_message()
    local_hash = load_local_commit_hash()
    if latest_hash == local_hash:
        print('Sama versio, ei paivitysta.')
        return
    os.chdir('/')
    tree = pull_git_tree()
    for i in tree['tree']:
        if i['type'] == 'tree':
            try:
                os.mkdir(i['path'])
            except:
                pass
        elif i['path'] not in ignore:
            try:
                os.remove(i['path'])
            except:
                pass
            pull(i['path'], raw + i['path'])
    t = get_finland_time()
    timestamp = f"{t[0]:04d}/{t[1]:02d}/{t[2]:02d} - {t[3]:02d}:{t[4]:02d}:{t[5]:02d}"
    with open('ugit_log.txt', 'a') as logfile:
        logfile.write(f'Timestamp: {timestamp}\n')
        logfile.write(f'Update ID: {latest_hash}\n')
        logfile.write(f'Update message: {commit_message}\n\n')
    time.sleep(5)
    # machine.reset() poistettu

def wificonnect(ssid=ssid, password=password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        time.sleep(1)
    if wlan.status() != 3:
        print('Yhteys epaonnistui')
    else:
        print('Yhdistetty')
    return wlan

def pull_git_tree(tree_url=call_trees_url, raw=raw):
    headers = {'User-Agent': 'ota-pico'}
    if len(github_token) > 0:
        headers['authorization'] = f"bearer {github_token}"
    r = urequests.get(tree_url, headers=headers)
    data = json.loads(r.content.decode('utf-8'))
    return data