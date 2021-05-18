#!/usr/bin/env python3

import json
from typing import List

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from os.path import dirname, abspath
from pathlib import Path

ROOT_DIR = dirname(dirname(abspath(__file__)))
checks_path = Path(ROOT_DIR, "lib", "checks.json")
challenges_path = Path(ROOT_DIR, "lib", 'challenges')
tools_path = dirname(abspath(__file__))
failed_povs = Path('povs_res2.txt')


def failing_neg_tests():
    neg_tests_not_ok = []
    for c in challenges_path.iterdir():
        if c.is_dir():
            povs = [f.name for f in c.iterdir() if f.name.startswith('pov')]
            neg_checks = c / Path('neg_checks.txt')
            if neg_checks.exists():
                with neg_checks.open(mode='r') as nc:
                    nt = nc.read().split()
                    if not nt:
                        neg_tests_not_ok.append(c.name)
                        print(nt, povs, c.name)

    neg_tests_not_ok.sort()

    # with open('povs_not_working.txt', 'w') as pnw:
    #    for t in neg_tests_not_ok:
    #        pnw.write(f"{t}\n")

    return neg_tests_not_ok


# lists the challenges that failed or time-outed for exclusion
def excluded_challenges():
    if checks_path.exists():
        excluded = {}

        with checks_path.open(mode="r") as cp:
            checks = json.loads(cp.read())
            for k, v in checks.items():
                for s, t in v.items():
                    if s == 'passed':
                        if not t:
                            excluded[k] = v
                            break
                        if len([test for test in t if test.startswith('n')]) == 0:
                            print(k)
                            excluded[k] = v
                    elif t:
                        excluded[k] = v
                        break

            return excluded
    return None


# checks if challenge vulnerability is spread across multiple files
def multi_file_challenge(manifest_path: Path):
    with manifest_path.open(mode="r") as mp:
        files = mp.readlines()
        for file in files:
            print(file)
        return len(files) > 1


def excluded_challenges_2():
    tmp_path = Path('/tmp')
    multi_file_challenges = []

    for folder in tmp_path.iterdir():
        if folder.is_dir():
            names = folder.name.split("_")

            if names[0] == "check":
                challenge_name = '_'.join(names[1:])
                manifest_path = folder / Path(challenge_name, 'manifest.txt')

                if multi_file_challenge(manifest_path):
                    multi_file_challenges.append(challenge_name)

    multi_file_challenges.sort()
    excluded = set(multi_file_challenges + failing_neg_tests())
    # with open('excluded.txt', 'w') as ex:
    #    excluded = list(excluded)
    #    excluded.sort()
    #    for e in excluded:
    #        ex.write(f"{e}\n")

    # with open('multi_file_challenges.txt', 'w') as mfc:
    #    for c in multi_file_challenges:
    #        mfc.write(f"{c}\n")

    '''
    for challenge in excluded:
        c_path = challenges_path / Path(challenge)
        if c_path.exists() and c_path.is_dir():
            os.system(f"rm -rf {str(c_path)}")
    '''
    return excluded


def cwe_scores_plot():
    cwe_scores_path = tools_path / Path('cwe_scores.pkl')
    cwe_scores = pd.read_pickle(str(cwe_scores_path))
    cwe_scores['cid'] = cwe_scores.apply(lambda x: int(x['cwe_id'].split('-')[-1]), axis=1)
    cwe_scores.sort_values('cid')
    ax = cwe_scores.plot.scatter(x='cid', y="score", c='DarkBlue')
    #plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
    #         rotation_mode="anchor")
    plt.show()


def unit_tests_results_parsing():
    file = ROOT_DIR / Path('unit_tests_results.txt')
    with file.open(mode="r") as f:
        content = f.read()
        by_challenge = content.split("Challenge: ")
        parsed = {}

        for chal in by_challenge[1:]:
            lines = chal.splitlines()
            splitted = lines[2].split()

            if not int(splitted[1]) > 0:
                continue
            parsed[lines[0]] = ' '.join(splitted).split("AssertionError:")[-1][3:5]

        ordered = list(parsed.keys())
        ordered.sort()
        print(ordered)

#unit_tests_results_parsing()
#{'FSK_BBS': 'n2', 'TextSearch': 'n2', 'ASL6parse': 'n1', 'ValveChecks': 'n1', 'router_simulator': 'n2', 'Griswold': 'n3', 'TAINTEDLOVE': 'n1', 'PCM_Message_decoder': 'n1', 'Filesystem_Command_Shell': 'n1', 'Diary_Parser': 'n2'}


def get_povs_count():
    return {c.name: len([f.name for f in c.iterdir() if f.name.startswith('pov')]) for c in challenges_path.iterdir() if c.is_dir()}


def parse_failed_povs():
    with failed_povs.open(mode="r") as fp:
        lines = fp.read().splitlines(keepends=False)

    data = []

    for line in lines:
        line = line.replace('\n', '')
        row = line.split('|')
        # shorten err messages with long hash

        if 'not in' in row[-1]:
            msg_split = row[-1].split('.')
            row[-1] = msg_split[0] + '. Hash not in.'
        if 'expected' in row[-1]:
            msg_split = row[-1].split('.')
            row[-1] = msg_split[0] + '. Actual eip != to expected eip.'

        data.append(row)

    return pd.DataFrame(data, columns=['name', 'pov', 'msg'])


def donut_plot(dataframe: pd.DataFrame, data_key: str, title: str):
    from matplotlib import cm

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(aspect="equal"))
    cs_customer = cm.get_cmap('tab10')(np.linspace(0, 1, 5))
    data_grouped = dataframe.groupby([data_key]).size()
    data_grouped.plot.pie(wedgeprops=dict(width=0.2), startangle=90, colors=cs_customer, ax=ax, autopct='%.2f',
                          legend=True, fontsize=12, pctdistance=0.9)

    ax.set_title(title, fontdict={'fontsize': 16, 'fontweight': 'bold'})
    plt.axis('off')
    fig.tight_layout()
    #plt.savefig('donutplot2.png', dpi=100, format='png', bbox_inches='tight')
    plt.legend(loc='center')
    plt.show()


def bar_plot_types(dataframe: pd.DataFrame, data_keys_group: List[str], title: str):
    from matplotlib import cm
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(aspect="equal"))
    all_povs = pd.DataFrame([[k, v] for k, v in get_povs_count().items()], columns=['name', 'total'])
    cs_customer = cm.get_cmap('tab10')(np.linspace(0, 1, 5))
    joined = dataframe.join(all_povs.set_index('name'), on='name')
    joined.plot.bar(x='name', y='total', color='yellow', ax=ax)
    data_grouped = joined.groupby(data_keys_group)[data_keys_group[0]].count().unstack(data_keys_group[1]).fillna(0)
    data_grouped.plot.bar(stacked=True, ax=ax, color=cs_customer)
    ax.set_title(title, fontdict={'fontsize': 16, 'fontweight': 'bold'})
    fig.tight_layout()
    plt.legend(loc='best')
    ax.set_xlabel("Challenge name")
    ax.set_ylabel("Counts")

    #plt.savefig('donutplot2.png', dpi=100, format='png', bbox_inches='tight')
    plt.show()


def parse_failed_povs2():
    failed_povs_json = Path('povs_res.txt')
#    import json
    parsed = {}
    with failed_povs_json.open(mode='r') as fpj:
        for line in fpj.readlines():
            line_dict = eval(line)
            parsed.update(line_dict)

    return parsed


def get_code(chals: dict):
    patterns = {}

    for name, vals in chals.items():
        if len(vals) > 1:
            continue

        for test_name, outcome in vals.items():
            if 'gcov' in outcome:

                for fname, code_lines in outcome['gcov'].items():
                    #if fname not in ['main.c', 'service.c', 'pov.c']:
                    #    continue
                    pattern = 0
                    for code_line in code_lines:
                        if int(code_line[0]) > 1:
                            print(name, fname, code_line[1], code_line[-1])
                            if 'cgc_transmit' in code_line[-1]:
                                pattern += int(code_line[0])
                    if pattern > 1:
                        patterns[name+" "+fname] = pattern
    for n,p in patterns.items():
        print(n, p)


#data = parse_failed_povs()
#bar_plot_types(data, ['name', 'msg'], 'POVs Ratio by Type')
#donut_plot(data, 'msg', 'POVs Failing cause')

get_code(parse_failed_povs2())
