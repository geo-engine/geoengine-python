# Readme

This set of notebooks contains the code for training a random forest model to classifiy field usage based on Sentinel-2 data.
The model is trained on field data for NRW, Germany from [EuroCrops](https://www.eurocrops.tum.de/). The EuroCrops data is available under the [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/). It can be downloaded from [here](https://github.com/maja601/EuroCrops#vectordata_zenodo).

## Preparation

First, the field polygons are converted into points and prepared for the use-case.
[This notebook](./nrw_crop_extern_prep_data.ipynb) contains the code for this step.

## Sentinel Data Extraction

We create two notebooks to extract the Sentinel-2 data for the points. The first notebook uses multiple workflow steps to attach the Sentinel-2 data to the points. The second notebook uses a single workflow step to attach the Sentinel-2 data to the points.

Both notebooks use the same area of interest and share the same code to generate workflows.

### Multiple Workflow Steps

This notebook "[nrw_crop_extern_s2_workflow_to_datasets] (./nrw_crop_extern_s2_workflow_to_datasets.ipynb)" contains the code to attach the Sentinel-2 data to the points using multiple steps.

First, the area of interest is defined.
Then, workflows are created that download the Sentinel-2 data of the bands 02, 03, 04, and 08 for the area of interest.
The resulting raster time-series is stored as a new datasets.

As a next step, for each band as well as the NDVI, which is calculated using an expression on band 4 and 8, a workflow is run to aggregates the raster data to monthly means.
Again, the resulting time-series is stored as a new dataset.

As a last step, the datasets are attached to the points.
Using the Geo Engine Python package, the point data is send to the Geo Engine.
Then a workflow is defined that uses the points and the aggregated bands datasets as input and creates a point-time-series as output.

This workflow is then queried from python and the resultng point data is stored in a gpkg file.

### Single Workflow Step

This notebook "[nrw_crop_extern_s2_workflow] (./nrw_crop_extern_s2_workflow.ipynb)" contains the code to attach the Sentinel-2 data to the points using a single workflow step.

We use the same area of interest as in the previous notebook.

First, the point data is send to the Geo Engine.
Then a workflow is defined that includes all the previous steps:
It has sources that provide Sentinel-2 data of the bands 02, 03, 04, and 08.
The NDVI is created using an expression on band 4 and 8.
All these inputs, as well as the NDVI, are aggregated to monthly means.
Finally, the point data is attached to the points using the raster-vector join.

The resulting qorkflow is queried with the area of interest from python and the resultng point data is stored in a gpkg file.

## Random Forest Training

The notebook "[nrw_crop_extern_train] (./nrw_crop_extern_train.ipynb)" contains the code to train a random forest model to classify the field usage based on the Sentinel-2 data attached to the points.

The notebook first loads the point data from the gpkg file.
Then, the data is split into a training and a test set.
The training set is used to train the model.
The test set is used to evaluate the model.
