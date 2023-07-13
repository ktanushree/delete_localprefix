#!/usr/bin/env python
"""
Prisma SD-WAN: Delete local security prefix binding & prefixes
Author: tkamath@paloaltonetworks.com

"""
import sys
import os
import argparse
import cloudgenix
import datetime
import pandas as pd

GLOBAL_MY_SCRIPT_NAME = "Prisma SD-WAN: Delete zombie local security prefix binding & prefixes"
GLOBAL_MY_SCRIPT_VERSION = "v1.0"
CSV_HEADER=["pf_name"]


# Import CloudGenix Python SDK
try:
    import cloudgenix
except ImportError as e:
    cloudgenix = None
    sys.stderr.write("ERROR: 'cloudgenix' python module required. (try 'pip install cloudgenix').\n {0}\n".format(e))
    sys.exit(1)

# Check for cloudgenix_settings.py config file in cwd.
sys.path.append(os.getcwd())
try:
    from cloudgenix_settings import CLOUDGENIX_AUTH_TOKEN

except ImportError:
    # if cloudgenix_settings.py file does not exist,
    # Get AUTH_TOKEN/X_AUTH_TOKEN from env variable, if it exists. X_AUTH_TOKEN takes priority.
    if "X_AUTH_TOKEN" in os.environ:
        CLOUDGENIX_AUTH_TOKEN = os.environ.get('X_AUTH_TOKEN')
    elif "AUTH_TOKEN" in os.environ:
        CLOUDGENIX_AUTH_TOKEN = os.environ.get('AUTH_TOKEN')
    else:
        # not set
        CLOUDGENIX_AUTH_TOKEN = None


# Handle differences between python 2 and 3. Code can use text_type and binary_type instead of str/bytes/unicode etc.
if sys.version_info < (3,):
    text_type = unicode
    binary_type = str
else:
    text_type = str
    binary_type = bytes

ngfwlocalprefix_id_name = {}
ngfwlocalprefix_name_id = {}
site_id_name = {}
site_name_id = {}


def create_dicts(cgx_session):

    #
    # Sites
    #
    resp = cgx_session.get.sites()
    if resp.cgx_status:
        itemlist = resp.cgx_content.get("items", None)
        for item in itemlist:
            site_id_name[item["id"]] = item["name"]
            site_name_id[item["name"]] = item["id"]
    else:
        print("ERR: Could not retrieve Sites")
        cloudgenix.jd_detailed(resp)

    #
    # NGFW Local Prefix
    #
    resp = cgx_session.get.ngfwsecuritypolicylocalprefixes_t()
    if resp.cgx_status:
        itemlist = resp.cgx_content.get("items", None)
        for item in itemlist:
            ngfwlocalprefix_id_name[item["id"]] = item["name"]
            ngfwlocalprefix_name_id[item["name"]] = item["id"]

    else:
        print("ERR: Could not retrieve Security Local Prefix Filters")
        cloudgenix.jd_detailed(resp)

    return

def remove_binding(cgx_session, filename):
    pfdata = pd.read_csv(filename)
    prefix_filters = pfdata.pf_name.unique()

    for pf in prefix_filters:
        if pf in ngfwlocalprefix_name_id.keys():
            pfid = ngfwlocalprefix_name_id[pf]

            data = {
                "query_params":{"prefix_id":{"eq":pfid}},
                "limit":10,
                "dest_page":1,
                "getDeleted":False,
                "retrieved_fields_mask":False,
                "retrieved_fields":[]
            }

            resp = cgx_session.post.ngfwsecuritypolicylocalprefixes_query(data=data)
            if resp.cgx_status:
                bindings = resp.cgx_content.get("items", None)
                if bindings is not None:
                    if len(bindings) > 0:
                        print("{}".format(pf))

                        for binding in bindings:
                            sid = binding.get("site_id")
                            sname = sid
                            if sid in site_id_name.keys():
                                sname = site_id_name[sid]
                            else:
                                print("\tWARN: Site name not found. Removing zombie association from {}".format(sid))

                            resp = cgx_session.delete.site_ngfwsecuritypolicylocalprefixes(site_id=sid, ngfwsecuritypolicylocalprefix_id=binding["id"])
                            if resp.cgx_status:
                                print("\t{}: Binding removed".format(sname))

                            else:
                                print("ERR: Could not remove binding for prefix filter {} from site {}".format(pf, sname))
                                cloudgenix.jd_detailed(resp)
                    else:
                        print("{} not bound to any site".format(pf))

            else:
                print("ERR: Could not retrieve prefix filter bindings for {}".format(pf))
                cloudgenix.jd_detailed(resp)

        else:
            print("ERR: Prefix {} not found. Ignoring this prefix.".format(pf))

    return

def delete_localprefixfilter(cgx_session, filename):
    pfdata = pd.read_csv(filename)
    prefix_filters = pfdata.pf_name.unique()
    for pf in prefix_filters:
        if pf in ngfwlocalprefix_name_id.keys():
            pfid = ngfwlocalprefix_name_id[pf]
            resp = cgx_session.delete.ngfwsecuritypolicylocalprefixes(ngfwsecuritypolicylocalprefix_id=pfid)
            if resp.cgx_status:
                print("{} deleted".format(pf))
            else:
                print("ERR: Could not delete prefix filter {}".format(pf))
                cloudgenix.jd_detailed(resp)
        else:
            print("ERR: Prefix {} not found. Ignoring this prefix.".format(pf))

    return

def go():
    """
    Stub script entry point. Authenticates CloudGenix SDK
    :return: No return
    """

    # Parse arguments
    parser = argparse.ArgumentParser(description="{0} ({1})".format(GLOBAL_MY_SCRIPT_NAME, GLOBAL_MY_SCRIPT_VERSION))

    ####
    #
    # End custom cmdline arguments
    #
    ####

    controller_group = parser.add_argument_group('API', 'These options change how this program connects to the API.')
    controller_group.add_argument("--controller", "-C",
                                  help="Controller URI, ex. https://api.elcapitan.cloudgenix.com",
                                  default=None)

    login_group = parser.add_argument_group('Login', 'These options allow skipping of interactive login')

    login_group.add_argument("--insecure", "-I", help="Do not verify SSL certificate",
                             action='store_true',
                             default=False)
    login_group.add_argument("--noregion", "-NR", help="Ignore Region-based redirection.",
                             dest='ignore_region', action='store_true', default=False)


    # Commandline for CSV file name
    pf_group = parser.add_argument_group('Prefix Filter CSV', 'CSV file containing prefix filters information')
    pf_group.add_argument("--filename", "-F", help="Name of the file with path.", default=None)
    pf_group.add_argument("--resource", "-R", help="Allowed value: security, path, qos, nat", default="security")
    pf_group.add_argument("--action", "-A", help="Allowed Actions: delete_prefix, delete_binding")

    ############################################################################
    # Parse Arguments
    ############################################################################
    args = vars(parser.parse_args())
    ############################################################################
    # Instantiate API & establish session
    ############################################################################
    cgx_session = cloudgenix.API(controller=args["controller"], ssl_verify=args["insecure"])

    if CLOUDGENIX_AUTH_TOKEN:
        cgx_session.interactive.use_token(CLOUDGENIX_AUTH_TOKEN)
        if cgx_session.tenant_id is None:
            print("AUTH_TOKEN login failure, please check token.")
            sys.exit()
    else:
        print("ERR: Auth token not found. Please provide a valid auth token")
        sys.exit()

    ############################################################################
    # Instantiate API & establish session
    ############################################################################
    # get time now.
    curtime_str = datetime.datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S')
    # create file-system friendly tenant str.
    tenant_str = "".join(x for x in cgx_session.tenant_name if x.isalnum()).lower()

    prefixfilter_csv = args['filename']
    if prefixfilter_csv is None:
        print("Please provide CSV filename with prefix filter information")
        cgx_session.get.logout()
        sys.exit()
    else:
        if not os.path.isfile(prefixfilter_csv):
            print("ERR: File {} does not exist. Please enter the accurate file path".format(prefixfilter_csv))
            sys.exit()
        else:
            pfdata = pd.read_csv(prefixfilter_csv)
            columns = list(pfdata.columns)
            if "pf_name" not in columns:
                print("ERR: Invalid CSV file. File does not contain mandatory header: pf_name")
                sys.exit()

    action = args["action"]
    if action is None:
        print("ERR: Please provide an action. Allowed values: delete_prefix, delete_binding")
        sys.exit()

    elif action not in ["delete_prefix", "delete_binding"]:
        print("ERR: Invalid action. Allowed values: delete_prefix, delete_binding")
        sys.exit()

    ############################################################################
    # Create Translation Dicts
    ############################################################################
    create_dicts(cgx_session)

    ############################################################################
    # Remove zombie associations
    ############################################################################
    if action == "delete_binding":
        remove_binding(cgx_session=cgx_session, filename=prefixfilter_csv)

    elif action == "delete_prefix":
        remove_binding(cgx_session=cgx_session, filename=prefixfilter_csv)
        delete_localprefixfilter(cgx_session=cgx_session, filename=prefixfilter_csv)


if __name__ == "__main__":
    go()
