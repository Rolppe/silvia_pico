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

def get_latest_commit_hash():
    headers = {'User-Agent': 'ota-pico'}
    if len(github_token) > 0:
        headers['authorization'] = f"bearer {github_token}"
    r = urequests.get(commit_url, headers=headers)
    data = json.loads(r.content.decode('utf-8'))
    return data['sha']

def load_local_commit_hash():
    try:
        with open('ugit_log.txt', 'r') as f:
            content = f.read()
            for line in content.splitlines():
                if line.startswith('Last commit: '):
                    return line.split('Last commit: ')[1].strip()
    except:
        pass
    return None

def save_local_commit_hash(log, sha):
    log.append(f'Last commit: {sha}')

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

def pull_all(tree=call_trees_url, raw=raw, ignore=ignore, isconnected=False):
    if not isconnected:
        wlan = wificonnect()
        time.sleep(2)
        ntptime.settime()
    latest_hash = get_latest_commit_hash()
    local_hash = load_local_commit_hash()
    if latest_hash == local_hash:
        print('Sama versio, ei paivitysta.')
        return
    os.chdir('/')
    tree = pull_git_tree()
    log = []
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
            t = time.localtime()
            timestamp = f"{t[0]:04d}/{t[1]:02d}/{t[2]:02d} - {t[3]:02d}:{t[4]:02d}:{t[5]:02d}"
            pull(i['path'], raw + i['path'])
            log.append(f'{timestamp} {i["path"]} paivitetty')
    save_local_commit_hash(log, latest_hash)
    logfile = open('ugit_log.txt', 'w')
    logfile.write('\n'.join(log))
    logfile.close()
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