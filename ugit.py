import os
import urequests
import json
import hashlib
import machine
import time
import network
from machine import Pin
from secrets import ssid, password, github_user, github_repo, github_token

default_branch = 'master'
ignore_files = ['ugit.py', 'secrets.py', '.DS_Store']
ignore = ignore_files
giturl = f'https://github.com/{github_user}/{github_repo}'
call_trees_url = f'https://api.github.com/repos/{github_user}/{github_repo}/git/trees/{default_branch}?recursive=1'
raw = f'https://raw.githubusercontent.com/{github_user}/{github_repo}/{default_branch}/'

led = Pin("LED", Pin.OUT)

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
    changed = False
    if not isconnected:
        wlan = wificonnect()
    os.chdir('/')
    tree = pull_git_tree()
    internal_tree = build_internal_tree()
    log = []
    for i in tree['tree']:
        if i['type'] == 'tree':
            try:
                os.mkdir(i['path'])
            except:
                pass
        elif i['path'] not in ignore:
            local_item = next((item for item in internal_tree if item[0] == i['path']), None)
            if local_item and local_item[1] == i['sha']:
                internal_tree.remove(local_item)
            else:
                if local_item:
                    os.remove(i['path'])
                    internal_tree.remove(local_item)
                    log.append(f'{i["path"]} poistettu ja paivitetty')
                else:
                    log.append(f'{i["path"]} paivitetty')
                pull(i['path'], raw + i['path'])
                changed = True
    if len(internal_tree) > 0:
        for item in internal_tree:
            try:
                os.remove(item[0])
                log.append(f'{item[0]} poistettu')
                changed = True
            except:
                pass
    logfile = open('ugit_log.py', 'w')
    logfile.write(str(log))
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

def build_internal_tree():
    internal_tree = []
    os.chdir('/')
    for i in os.listdir():
        add_to_tree(i, internal_tree)
    return internal_tree

def add_to_tree(dir_item, internal_tree):
    if is_directory(dir_item):
        if len(os.listdir(dir_item)) >= 1:
            os.chdir(dir_item)
            for i in os.listdir():
                add_to_tree(i, internal_tree)
            os.chdir('..')
    else:
        if os.getcwd() != '/':
            subfile_path = os.getcwd() + '/' + dir_item
        else:
            subfile_path = dir_item
        try:
            internal_tree.append([subfile_path, get_hash(subfile_path)])
        except:
            pass

def get_hash(file):
    with open(file, 'rb') as o_file:
        r_file = o_file.read()
        header = b"blob " + str(len(r_file)).encode() + b"\0"
        sha1obj = hashlib.sha1(header + r_file)
        return sha1obj.hexdigest()

def is_directory(file):
    try:
        stat = os.stat(file)
        return (stat[0] & 0x4000) != 0
    except:
        return False

def pull_git_tree(tree_url=call_trees_url, raw=raw):
    headers = {'User-Agent': 'ota-pico'}
    if len(github_token) > 0:
        headers['authorization'] = f"bearer {github_token}"
    r = urequests.get(tree_url, headers=headers)
    data = json.loads(r.content.decode('utf-8'))
    return data