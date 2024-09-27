import pypsa
import matplotlib.pyplot as plt
plt. style.use("bmh")

n1=pypsa.Network("/Users/katjapelzer/Thesis/MA_Git/outputs/base_2045_0CO2/postnetworks/base_s_39_lvopt___2030.nc")
n2=pypsa.Network("/Users/katjapelzer/Thesis/MA_Git/outputs/base_2045_0CO2/postnetworks/base_s_39_lvopt___2035.nc")
n3=pypsa.Network("/Users/katjapelzer/Thesis/MA_Git/outputs/base_2045_0CO2/postnetworks/base_s_39_lvopt___2045.nc")


#Grouped 
g_links=n3.links.groupby("carrier").p_nom_opt.sum() /1e3 # GW instead of MW
g_links.to_csv("/Users/katjapelzer/Thesis/MA_Git/test_outputs/links_2045_g.csv")

g_generators=n3.generators.groupby("carrier").p_nom_opt.sum() /1e3 # GW instead of MW
g_generators.to_csv("/Users/katjapelzer/Thesis/MA_Git/test_outputs/generators_2045_g.csv")

g_storage_units=n3.storage_units.groupby("carrier").p_nom_opt.sum() /1e3 # GW instead of MW
g_storage_units.to_csv("/Users/katjapelzer/Thesis/MA_Git/test_outputs/storage_units_2045_g.csv")



n3.buses.to_csv("/Users/katjapelzer/Thesis/MA_Git/test_outputs/buses_2045.csv")
n3.links.to_csv("/Users/katjapelzer/Thesis/MA_Git/test_outputs/links_2045.csv")
n3.storage_units.to_csv("/Users/katjapelzer/Thesis/MA_Git/test_outputs/storage_units_2045.csv")
n3.stores.to_csv("/Users/katjapelzer/Thesis/MA_Git/test_outputs/stores_2045.csv")

n3.links_t.p0.to_csv("/Users/katjapelzer/Thesis/MA_Git/test_outputs/links_2045_t.p0.csv")
n3.links_t.p1.to_csv("/Users/katjapelzer/Thesis/MA_Git/test_outputs/links_2045_t.p1.csv")
print(n1.objective)
print(n2.objective)
print(n3.objective)

print(n3)
