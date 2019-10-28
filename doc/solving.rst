##########################################
Solving Networks
##########################################

After generating and simplifying the networks they can be solved through the rule :mod:`solve_network`  by using the collection rule :mod:`solve_all_elec_networks`. Moreover, networks can be solved for another focus with the derivative rules :mod:`solve_network`  by using the collection rule :mod:`trace_solve_network` to log changes during iterations and :mod:`solve_network`  by using the collection rule :mod:`solve_operations_network` for dispatch-only analyses on an already solved network.

.. toctree::
   :caption: Overview

   solving/solve_network
   solving/trace_solve_network
   solving/solve_operations_network