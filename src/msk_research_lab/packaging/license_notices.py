"""Third-party software license aggregation and manifest for MSK Research Lab OS."""

from pathlib import Path
from typing import Dict, List, Optional
from msk_research_lab.core.config import get_config

THIRD_PARTY_LICENSES: List[Dict[str, str]] = [
    {
        "component": "DBCLS BodyParts3D / Z-Anatomy 3D Anatomical Meshes (anatomy.glb)",
        "upstream_author": "DBCLS (Database Center for Life Science, University of Tokyo) & Z-Anatomy Project / watercmy",
        "license_name": "Creative Commons Attribution-ShareAlike 2.1 Japan (CC BY-SA 2.1 JP) / CC BY-SA 4.0",
        "notice": """BodyParts3D, Copyright (c) 2008-2026 Database Center for Life Science (DBCLS), University of Tokyo.
Licensed under the Creative Commons Attribution-ShareAlike 2.1 Japan license.
Z-Anatomy, Copyright (c) Gauthier Kervyn and contributors.
Derived and bundled as research and educational anatomical geometry.""",
    },
    {
        "component": "spacejohnlf TCM Acupoints 3D Mannequin Mesh (body.glb)",
        "upstream_author": "spacejohnlf (spacejohnlf--tcm-acupoints)",
        "license_name": "MIT License",
        "notice": """MIT License
Copyright (c) 2024 spacejohnlf
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.""",
    },
    {
        "component": "MediaPipe Pose Landmarker Lite (pose_landmarker_lite.task)",
        "upstream_author": "Google LLC",
        "license_name": "Apache License 2.0",
        "notice": """Copyright 2023-2026 Google LLC
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at:
http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.""",
    },
    {
        "component": "Three.js (three.min.js, GLTFLoader.js, OrbitControls.js)",
        "upstream_author": "Ricardo Cabello (mrdoob) and Three.js contributors",
        "license_name": "MIT License",
        "notice": """The MIT License
Copyright (c) 2010-2026 Three.js Authors
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.""",
    },
    {
        "component": "FastAPI, Starlette & Pydantic",
        "upstream_author": "Sebastián Ramírez, Encode OSS, and Samuel Colvin",
        "license_name": "MIT License",
        "notice": """Copyright (c) 2018 Sebastián Ramírez, Encode OSS, Samuel Colvin.
Licensed under the MIT License.""",
    },
    {
        "component": "OpenCV (Open Source Computer Vision Library)",
        "upstream_author": "OpenCV team and contributors",
        "license_name": "Apache License 2.0",
        "notice": """Copyright (C) 2000-2026, Intel Corporation, all rights reserved.
Copyright (C) 2009-2026, Willow Garage Inc., all rights reserved.
Licensed under the Apache License, Version 2.0.""",
    },
    {
        "component": "SQLite 3",
        "upstream_author": "D. Richard Hipp and SQLite contributors",
        "license_name": "Public Domain",
        "notice": """SQLite is dedicated to the public domain. All code and documentation in SQLite
has been dedicated to the public domain by the authors.""",
    },
]


def format_license_notices() -> str:
    """Format all aggregated third-party licenses into a single text document."""
    lines = [
        "================================================================================",
        "MSK RESEARCH LAB OS — THIRD-PARTY SOFTWARE AND ASSET LICENSE NOTICES",
        "================================================================================",
        "This workstation bundles and utilizes third-party open source software,",
        "computational models, and anatomical geometry assets. Applicable notices",
        "and licenses are documented below pursuant to their distribution terms.",
        "================================================================================",
        "",
    ]

    for item in THIRD_PARTY_LICENSES:
        lines.append("-" * 80)
        lines.append(f"Component: {item['component']}")
        lines.append(f"Author / Origin: {item['upstream_author']}")
        lines.append(f"License: {item['license_name']}")
        lines.append("-" * 80)
        lines.append(item["notice"].strip())
        lines.append("")
        lines.append("")

    return "\n".join(lines)


def write_license_notices_file(output_path: Optional[Path] = None) -> Path:
    """Write license notices document to disk."""
    if output_path is None:
        cfg = get_config()
        output_path = cfg.storage.root_dir / "dist" / "LICENSE_NOTICES.txt"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    text = format_license_notices()
    output_path.write_text(text, encoding="utf-8")
    return output_path
