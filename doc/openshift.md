# Openshift

Tips for interacting with OpenShift.

## Create ServiceAccount

Follow this guide to create a ```service account``` in the ```modeling``` environment (oc login + oc project modeling) to interact with the Openshift API:

https://docs.openshift.com/enterprise/3.0/dev_guide/service_accounts.html

In short:

```
$ more sa.json
{
  "apiVersion": "v1",
  "kind": "ServiceAccount",
  "metadata": {
    "name": "modeling-bot"
  }
}
```

```
oc create -f sa.json
```

Assign ```admin``` role to the new service account (allow reads and writes).

```
oc policy add-role-to-user admin system:serviceaccount:modeling:modeling-bot
```

Finally get the service account token and add it to this project's openshift.yml file

```
oc describe secret modeling-bot-token-XXXX
```

## Automodeling services management

Since all different objects of the deployment (service, route, and deployment config) are labeled with ```label:@{APP}```:
- you can request the objects to delete by typing:
 ```
 oc get all -l app=scheduler
 ```

- and you can delete all by typing:
```
oc delete all -l app=scheduler
```
