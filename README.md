<p align="center">
  <img src="imgs/Carbon_Explorer_logo.png" width="1000">
  <br />
</p>

_Carbon Explorer_ evaluates solutions make datacenters operate on renewable energy holistically by including embodied and operational footprints. Solutions _Carbon Explorer_ supports include:
* Capacity sizing with a mix of solar and wind power
* Battery storage
* Carbon aware workload scheduling

Details can be found here:
[A Holistic Approach for Designing Carbon Aware Datacenters (Acun et al, 2022).](https://arxiv.org/abs/2201.10036)
\
\
\
The repository contains two notebooks:
* [**EIA_Energy_Data_Analysis.ipynb**](https://github.com/facebookresearch/CarbonExplorer/blob/main/EIA_Energy_Data_Analysis.ipynb) analyses [EIA's hourly renewable energy data](https://www.eia.gov/opendata/bulkfiles.php).
* [**Carbon_Explorer.ipynb**](https://github.com/facebookresearch/CarbonExplorer/blob/main/Carbon_Explorer.ipynb) combines EIA's data with DC power simulations, evaluates the solutions listed above and finally produces embodied and operational footprint analysis.
\
&nbsp;
## Citation
Carbon Explorer is accepted at [ASPLOS'23](https://asplos-conference.org/). Please cite as:
``` bibtex
@article{acun2022holistic,
  title={Carbon Explorer: A Holistic Approach for Designing Carbon Aware Datacenters},
  author={Acun, Bilge and Lee, Benjamin and Maeng, Kiwan and Chakkaravarthy, Manoj and Gupta, Udit and Brooks, David and Wu, Carole-Jean},
  journal={Proceedings of the 28th ACM International Conference on Architectural Support for Programming Languages and Operating Systems},
  year={2023}
}
```

### License
_Carbon Explorer_ is CC-BY-NC licensed.
