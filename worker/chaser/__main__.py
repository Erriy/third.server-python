#!/usr/bin/env python3
# -*- coding=utf-8 -*-
import os
import click
from prettytable import PrettyTable
from tqdm import tqdm
from engine import chasers, download as do_download


@click.group()
def cmd():
    pass


@cmd.command()
def list_rule():
    table = PrettyTable(['rule'])
    list(map(lambda x: table.add_row([x]), chasers.keys()))
    print(table)


@cmd.command()
@click.argument('key')
def search(key):
    table = PrettyTable(['name', 'rule', 'epid'])
    for c in chasers.values():
        for r in c.search(key):
            table.add_row([
                r.get('name'),
                r.get('rule'),
                r.get('epid'),
            ])

    print(table)


@cmd.command()
@click.option('--rule', '-r', required=True, type=str)
@click.option('--epid', '-e', required=True, type=str)
@click.option('--vid', '-v', required=False, default='', type=str)
@click.option('--download', flag_value=True, default=False)
@click.option('--output', default='./download', help='指定下载地址')
def episodes(rule, epid, vid, download, output):
    results = chasers[rule].episodes(epid)
    table = PrettyTable(['name', 'rule', 'epid', 'vid'])
    for r in results:
        table.add_row([
            r.get('name'),
            r.get('rule'),
            epid,
            r.get('vid'),
        ])
    print(table)
    if not download:
        return
    if not os.path.exists(output):
        os.makedirs(output)
    vid = list(filter(lambda x: x, vid.split(',')))
    for r in results:
        if len(vid) and r['vid'] not in vid:
            continue
        print('downloading {}-{}.{}'.format(r['name'], epid, r['vid']))
        path = os.path.join(output, r['name'])
        url = chasers[rule].video(epid, r['vid'])
        with tqdm(total=100) as pbar:
            def progress(d):
                percent = 0
                if d.get("downloaded_bytes") and d.get('total_bytes'):
                    percent = d.get("downloaded_bytes")/d.get('total_bytes')
                pbar.update(percent)

            do_download(url, path+'.mp4', progress)




if __name__ == "__main__":
    # todo 借口修改为search 和download，download中可以指定下载规则
    cmd()

