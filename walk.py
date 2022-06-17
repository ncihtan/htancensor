import synapseclient
import re
import subprocess
syn = synapseclient.Synapse()
syn.login()

def run_censor(id):
    censor_exc = subprocess.run(
        ['python','htancensor/synapsecensor_hms.py', id], 
        capture_output = True, text=True
        )
    print(censor_exc.stdout)
    print(censor_exc.stdout)

for entity in syn.getChildren('syn25808655'):
    if re.match(r'.+svs$', entity['name']):
        print(f"Deidentifying {entity['id']}: {entity['name']}")
        run_censor(entity['id'])
        print(f"\tCompleted deidentification of {entity['id']}")
print("Complete")