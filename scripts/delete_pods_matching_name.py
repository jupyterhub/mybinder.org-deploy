from subprocess import check_output, call
import argparse

parser = argparse.ArgumentParser(description="Quickly delete pods with a name that includes `match`.")
parser.add_argument("match", help="A string to match to pod names.")
parser.add_argument("--delete", dest='do_delete', action='store_true', help="Whether to run the `kubectl delete` command.")
args = parser.parse_args()

match = args.match
do_delete = args.do_delete
# The -l matches on labels, and all user pods have the label component=singleuser-server
pods = check_output('kubectl --namespace=prod get pod -o name -l component=singleuser-server'.split())

for line in pods.split('\n'):
    if match in line:
        name = line.split()[0]
        command = 'kubectl --namespace=prod delete {}'.format(name)
        if do_delete is True:
            call(command.split())  # When you know it'll work!
        else:
            print(command)  # For making sure your command is correct
