'''This module contains blueprints for workflows that are not yet stable.'''

import geoengine as ge


def sentinel2_cloud_free_band(band_name, provider="5779494c-f3a2-48b3-8a2d-5fbba8c5b6c5", utm_zone="UTM32N"):
    '''Creates a workflow for a cloud free band from Sentinel 2 data.'''
    band_source = ge.unstable.workflow_operators.GdalSource(
        dataset=ge.api.ExternalDataId(
            type="external",
            providerId=provider,
            layerId=f"{utm_zone}:{band_name}"
        )
    )
    scl_source = ge.unstable.workflow_operators.GdalSource(
        dataset=ge.api.ExternalDataId(

            type="external",
            providerId=provider,
            layerId=f"{utm_zone}:SCL"
        )
    )
    # [sen2_mask == 3 |sen2_mask == 7 |sen2_mask == 8 | sen2_mask == 9 |sen2_mask == 10 |sen2_mask == 11 ]
    cloud_free = ge.unstable.workflow_operators.Expression(
        expression=" if (B == 3 || (B >= 7 && B <= 11)) { NODATA } else { A }",
        output_type="U16",
        sources={
            "a": band_source,
            "b": scl_source,
        }
    )

    return cloud_free
