import pypsa
import matplotlib.pyplot as plt
plt. style.use("bmh")

n=pypsa.Network("/Users/katjapelzer/pypsa-eur-current/results/test-sector-myopic/postnetworks/base_s_20_lvopt___2045.nc")
n.generators.to_csv("/Users/katjapelzer/Thesis/MA_Git/test_outputs/generators.csv")
#print(n.generators.grouby("carrier").p_nom_opt())

    
# Access the constraints from the optimization model
constraints = n.model.constraints

# Check if the 'bau_maxcaps' constraint has been added
if "bau_maxcaps" in constraints:
    print("BAU max capacity constraint found!")
else:
    print("BAU max capacity constraint not found.")