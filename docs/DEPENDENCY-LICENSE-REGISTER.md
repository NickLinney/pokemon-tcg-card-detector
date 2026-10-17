# Dependency and License Register

This is an engineering inventory, not legal advice. Versions are the resolved
commissioned environment. Direct dependencies are pinned in `pyproject.toml`;
the full environment is frozen in `requirements.lock.txt`.

| Component | Version | Observed project/package license | Role |
|---|---:|---|---|
| TCGdex cards-database | v2.48.0 | MIT | Local reference metadata |
| EasyOCR | 1.7.2 | Apache-2.0 project | OCR orchestration |
| OpenCV Python headless | 4.12.0.88 | Apache-2.0 | Segmentation and local features |
| NumPy | 2.2.6 | BSD-3-Clause | Numeric operations |
| Pillow | 11.3.0 | HPND/Pillow | Image decoding and pHash input |
| ImageHash | 4.3.2 | BSD-2-Clause project | Perceptual hashing |
| RapidFuzz | 3.14.1 | MIT | Candidate text similarity |
| PyYAML | 6.0.2 | MIT | Template registry |
| jsonschema | 4.25.1 | MIT | Schema validation |
| pytest | 8.4.2 | MIT | Tests |
| PyTorch / torchvision | 2.14.1 / 0.29.1 | BSD-style project licenses plus bundled notices | EasyOCR runtime |
| SciPy / scikit-image | 1.18.1 / 0.26.0 | BSD-3-Clause | EasyOCR/image transitive runtime |
| Shapely | 2.2.0 | BSD-3-Clause plus GEOS notices | EasyOCR transitive runtime |

## OCR model artifacts

The following model files were downloaded by HTTPS from EasyOCR's declared
model locations and verified against EasyOCR's declared MD5 values. Their
SHA-256 digests are recorded for reproducibility:

| Model | SHA-256 |
|---|---|
| `craft_mlt_25k.pth` | `4a5efbfb48b4081100544e75e1e2b57f8de3d84f213004b14b85fd4b3748db17` |
| `japanese_g2.pth` | `afbb32b0485297de5a7c1f59aeecac12c69f32b15cedd3c3d8c2e8529de85af3` |

The model artifacts are excluded from Git. A separately explicit model/data
redistribution license was not established during this commission, so their
redistribution state is `EvidenceRequired`.
