import pypsa 
import matplotlib.pyplot as plt
plt. style.use("bmh")

n= pypsa.Network("/Users/katjapelzer/Thesis/MA_Git/pypsa-eur/results/test-elec/networks/elec_s_6_ec_lcopt_.nc")
# print(n.carriers)

n_base = pypsa.Network("/Users/katjapelzer/Thesis/MA_Git/pypsa-eur/resources/test/networks/base.nc")
# print(n_base.iterate_components())

print(n.carriers)

print(n.load_powerplants())