import getopt
import sys
import yaml
import os
import requests
from dotenv import load_dotenv
from packaging.version import parse, InvalidVersion
from termcolor import colored


# Create class so that YAML dumper doesn't create references <eyeroll>
class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


# Load configuration
load_dotenv(override=True)

api_key = os.environ["ELASTIC_API_KEY"]
endpoint = os.environ["KIBANA_ENDPOINT"]

# Set global header for Elastic API requests
headers = {"kbn-xsrf": "true",
           "Content-Type": "application/json",
           "Authorization": f"ApiKey {api_key}"}

# Create a global session object for requests to use HTTP keep-alive
s = requests.Session()


# Get list of Packages (Integrations) from Elastic Package Manager (EPM)
def get_packages():
    url = f"{endpoint}/api/fleet/epm/packages"
    r = s.get(url=url, headers=headers)
    if r.status_code == 200:
        return r.json()


def get_changelog(pkg_name: str, latest_version: str, current_version: str):
    url = f"{endpoint}/api/fleet/epm/packages/{pkg_name}/{latest_version}/changelog.yml"
    r = s.get(url=url, headers=headers)
    if r.status_code == 200:
        changelog = yaml.load(r.text, Loader=yaml.FullLoader)
        changelog_diff = []
        for change in changelog:
            try:
                if parse(change['version']) > parse(current_version):
                    changelog_diff.append(change)
            except InvalidVersion:
                continue
        return changelog_diff


def notify(upgrade_candidates: list):
    #print(upgrade_candidates)
    return


def main(argv):
    usage = 'integration-update-alert.py [-c] [--changelog]'
    changelog_flag = False
    try:
        opts, args = getopt.getopt(argv, ":hc", ["changelog"])
    except getopt.GetoptError:
        print(usage)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(usage)
            sys.exit()
        elif opt in ("-c", "--changelog"):
            changelog_flag = True

    upgrade_candidates = []
    packages = get_packages()
    for package in packages['items']:
        if 'installationInfo' in package.keys():
            cur_ver = package["installationInfo"]["version"]
            latest_ver = package["version"]
            name = package["name"]
            if parse(cur_ver) < parse(latest_ver):
                changelog = get_changelog(pkg_name=name, latest_version=latest_ver, current_version=cur_ver)
                p = {'name': name, 'latest_version': latest_ver, 'installed_version': cur_ver}
                print(f'Upgrade available for package: {colored(name, "cyan")}\n'
                      f'Latest version: {colored(latest_ver, "green")}\n'
                      f'Installed version: {cur_ver}')
                if changelog_flag:
                    print(f'Changelog:\n{yaml.dump(changelog, allow_unicode=True, default_flow_style=False, sort_keys=False, Dumper=NoAliasDumper)}\n')
                    p['changelog'] = changelog
                upgrade_candidates.append(p)
    notify(upgrade_candidates)


if __name__ == "__main__":
    main(sys.argv[1:])
