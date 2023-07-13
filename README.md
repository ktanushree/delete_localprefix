# delete_localprefix
This script is used to unbind local prefix filters from sites and delete them. 

#### Synopsis
This script is can be used to manage local prefix filter unbinding and deletion. The script behavior is governed by the action parameter. The prefix filters need to be provided in a CSV file, where the names need to be in a column with header **pf_name**.

Allowed actions are **delete_binding** and **delete_prefix**.

When the action is **delete_binding**, the script only unbinds the local prefix filters from all sites.
When the action is **delete_prefix**, the script will unbind and delete the local prefix filter.

Note: in version 1.0.0b1, only security prefix filters are supported. Also, in this version, the prefix filters will be unbound and removed from all sites.

#### Requirements
* Active Prisma SD-WAN Account
* Python >=3.6
* Python modules:
    * CloudGenix Python SDK >= 6.2.2b1 - <https://github.com/CloudGenix/sdk-python>
* pandas
  
#### License
MIT

#### Installation:
 - **Github:** Download files to a local directory, manually run `deletelocalprefix.py`. 

### Usage:
Remove local prefix filter bindings from all sites
```
./deletelocalprefix.py -F filename -A delete_binding
```

Remove local prefix filter bindings from all sites AND delete local prefix filter
```
./deletelocalprefix.py -F filename -A delete_prefix
```

Help Text:
```angular2
Tanushrees-MacBook-Pro:deletelocalprefix tanushreekamath$
Prisma SD-WAN: Delete local prefix binding & prefixes (v1.0)

optional arguments:
  -h, --help            show this help message and exit

API:
  These options change how this program connects to the API.

  --controller CONTROLLER, -C CONTROLLER
                        Controller URI, ex. https://api.elcapitan.cloudgenix.com

Login:
  These options allow skipping of interactive login

  --insecure, -I        Do not verify SSL certificate
  --noregion, -NR       Ignore Region-based redirection.

Prefix Filter CSV:
  CSV file containing prefix filters information

  --filename FILENAME, -F FILENAME
                        Name of the file with path.
  --resource RESOURCE, -R RESOURCE
                        Allowed value: security, path, qos, nat
  --action ACTION, -A ACTION
                        Allowed Actions: delete_prefix, delete_binding
Tanushrees-MacBook-Pro:deletelocalprefix tanushreekamath$ 


```

#### Version
| Version | Build | Changes |
| ------- | ----- | ------- |
| **1.0.0** | **b1** | Initial Release. |


#### For more info
 * Get help and additional Prisma SDWAN Documentation at <https://docs.paloaltonetworks.com/prisma/prisma-sd-wan>
 
