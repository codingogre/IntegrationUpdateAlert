import json
from dotenv import load_dotenv
import os
import requests
from packaging import version
from termcolor import colored

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


def notify(upgrade_candidates: list):
    print(upgrade_candidates)


def main():
    upgrade_candidates = []
    packages = get_packages()
    for package in packages['items']:
        if 'installationInfo' in package.keys():
            if version.parse(package['installationInfo']['version']) < version.parse(package['version']):
                print(f'Upgrade available for package: {colored(package["name"], "cyan")}\n'
                      f'  Latest version: {colored(package["version"], "green")}\n'
                      f'  Installed version: {package["installationInfo"]["version"]}')
                upgrade_candidates.append({'name': package["name"],
                                           'latest_version': package["version"],
                                           'installed_version': package["installationInfo"]["version"]})
    notify(upgrade_candidates)


if __name__ == "__main__":
    main()
