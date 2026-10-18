from pathlib import Path

import cv2
import numpy as np

from ptcg.localization import initialize_zone_observations, localize_zone_proposals
from ptcg.template_registry import TemplateRegistry


def test_edge_proposal_is_distinct_from_template_prior():
    template = TemplateRegistry(Path(__file__).parents[1] / "templates").resolve(
        "pokemon.generic.v1"
    )
    image = np.full((880, 630, 3), 255, dtype=np.uint8)
    cv2.rectangle(image, (55, 30), (300, 65), (0, 0, 0), 2)
    source_polygon = [[0, 0], [629, 0], [629, 879], [0, 879]]
    observations = initialize_zone_observations(
        template,
        source_polygon,
        {"glare_fraction": 0.0, "laplacian_variance": 100.0},
    )
    localize_zone_proposals(image, observations, source_polygon)

    title = observations["title"]
    assert title["localized"] is not None
    assert title["presence_state"] == "PRESENT"
    assert title["localization"]["independent_pixel_evidence"] is True
    assert title["localized"]["semantic_assignment_state"] == (
        "PROVISIONAL_TEMPLATE_CONDITIONED"
    )
    assert title["prior"]["normalized_pixel_rect"] != title["localized"][
        "normalized_pixel_rect"
    ]
