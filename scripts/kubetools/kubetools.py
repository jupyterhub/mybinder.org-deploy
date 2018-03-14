from subprocess import check_output, check_call
import pandas as pd

AGE_IN_MINS = {'s': 1/60., 'm': 1, 'h': 60, 'd': 60*24}

def _age_str_to_minutes(item):
    kind = item[-1]
    number = item[:-1]
    return AGE_IN_MINS[kind] * float(number)

def get_all(kind, ns='prod'):
    """Run `kubectl get <kind>` and return results as a DataFrame.
    
    Parameters
    ----------
    kind : str
        <kind> in `kubectl --namespace=<ns> get <kind>`
    ns : str
        <ns> in `kubectl --namespace=<ns> get <kind>`
        
    Returns
    -------
    df : DataFrame
        The results in a Pandas DataFrame
    """
    cmd = 'kubectl get {} -o wide --namespace={}'.format(kind, ns)
    out = check_output(cmd.split())
    lines = out.decode().split('\n')
    lines[0] = lines[0].lower()
    lines = [ii.split() for ii in lines]
    df = pd.DataFrame(lines[1:], columns=lines[0])
    df = df.query('name != None')
    df['age'] = df['age'].map(_age_str_to_minutes)
    return df

def delete(name, kind='pod', ns='prod', force=False, verbose=True):
    """Run `kubectl delete <name>`
    
    Parameters
    ----------
    name : str
        <name> in `kubectl --namespace=<ns> delete <kind> <name>`
    kind : str
        <kind> in `kubectl --namespace=<ns> delete <kind> <name>`
    ns : str
        <ns> in `kubectl --namespace=<ns> delete <kind> <name>`
    """
    cmd = 'kubectl --namespace={ns} delete {kind} {name}'.format(ns=ns, kind=kind, name=name)
    if force is True:
        cmd += ' --grace-period=0 --force'
    check_call(cmd.split())
    if verbose is True:
        print('Deleted pod: {name}'.format(name=name))