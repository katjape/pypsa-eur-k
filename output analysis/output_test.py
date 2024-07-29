import pypsa 
import matplotlib.pyplot as plt
plt. style.use("bmh")

n= pypsa.Network("/Users/katjapelzer/Thesis/MA_Git/pypsa-eur/results/test-elec/networks/elec_s_6_ec_lcopt_.nc")
# print(n.carriers)

n_coupled = pypsa.Network("/Users/katjapelzer/Thesis/MA_Git/pypsa-eur/results/test-sector-overnight/postnetworks/elec_s_5_lv1.5___2030.nc")

n_base = pypsa.Network("/Users/katjapelzer/Thesis/MA_Git/pypsa-eur/resources/test/networks/base.nc")
# print(n_base.iterate_components())

# print(n.carriers)

# print(n.load_powerplants())

# n_coupled_myopic=pypsa.Network("/Users/katjapelzer/Thesis/MA_Git/pypsa-eur/results/test-sector-myopic/postnetworks/elec_s_5_lv1.5___2040.nc")

# print (n_coupled_myopic.global_constraints)


#n_coupled_myopic.generators.to_csv("/Users/katjapelzer/Thesis/MA_Git/test files/output_myopic_generators.csv")

n = pypsa.Network("/Users/katjapelzer/Thesis/MA_Git/pypsa-eur/results/test-sector-overnight/postnetworks/elec_s_5_lv1.5___2030.nc")

n.links.to_csv("/Users/katjapelzer/Thesis/MA_Git/test files/solved network_overnight-links.csv")

link_summary = n.links.groupby("carrier").p_nom_opt.sum() /1e3
link_summary.to_csv("/Users/katjapelzer/Thesis/MA_Git/test files/solved network_overnight-links_grouped by.csv") # GW instead of MW

# print(n.generators)

generators_summary= n.generators.groupby("carrier").p_nom_opt.sum()
generators_summary.to_csv("/Users/katjapelzer/Thesis/MA_Git/test files/solved network_overnight-generators_grouped by.csv") # GW instead of MW

print(generators_summary)

