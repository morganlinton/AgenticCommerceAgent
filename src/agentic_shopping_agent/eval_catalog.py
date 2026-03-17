from __future__ import annotations


def _criterion(name: str, kind: str, weight: float) -> dict:
    return {"name": name, "kind": kind, "weight": weight}


def _scenario(
    *,
    scenario_id: str,
    title: str,
    query: str,
    budget: float | None,
    criteria: list[dict],
    notes: str | None = None,
    allowed_domains: list[str] | None = None,
    expectations: dict | None = None,
) -> dict:
    request = {
        "query": query,
        "criteria": criteria,
        "budget": budget,
        "currency": "USD",
        "location": "United States",
        "max_options": 4,
        "notes": notes,
        "allowed_domains": allowed_domains or [],
        "allow_open_web": False,
    }
    return {
        "id": scenario_id,
        "title": title,
        "request": request,
        "expectations": expectations or {},
    }


BUILTIN_EVAL_SCENARIOS = [
    _scenario(
        scenario_id="travel-headphones",
        title="Travel headphones under hard budget",
        query="wireless noise-cancelling headphones",
        budget=300,
        criteria=[
            _criterion("sound quality", "preference", 1.0),
            _criterion("battery life", "preference", 1.0),
            _criterion("active noise cancellation", "must_have", 1.5),
            _criterion("refurbished or used condition", "avoid", 1.2),
        ],
        notes="Prioritize long-flight comfort and avoid refurbished listings.",
        expectations={
            "min_recommended_source_count": 2,
            "required_verification_status": "verified",
            "required_criterion_names": ["sound quality", "battery life", "active noise cancellation"],
            "forbidden_recommended_name_terms": ["refurbished", "used", "renewed"],
        },
    ),
    _scenario(
        scenario_id="portable-charger",
        title="Portable charger for travel",
        query="portable charger",
        budget=120,
        criteria=[
            _criterion("battery capacity", "preference", 1.0),
            _criterion("charging speed", "preference", 1.0),
            _criterion("airline-friendly size", "must_have", 1.5),
            _criterion("bulky design", "avoid", 1.0),
        ],
        notes="Needs to fit easily in a personal item for travel.",
        expectations={
            "min_recommended_source_count": 2,
            "required_verification_status": "verified",
            "required_criterion_names": ["battery capacity", "charging speed", "airline-friendly size"],
        },
    ),
    _scenario(
        scenario_id="office-chair",
        title="Office chair with ergonomic support",
        query="ergonomic office chair",
        budget=450,
        criteria=[
            _criterion("lumbar support", "must_have", 1.5),
            _criterion("adjustability", "preference", 1.0),
            _criterion("mesh back or breathable material", "preference", 1.0),
            _criterion("poor warranty coverage", "avoid", 1.0),
        ],
        notes="Home office use for 8 hour workdays.",
        expectations={
            "min_recommended_source_count": 2,
            "required_verification_status": "verified",
            "required_criterion_names": ["lumbar support", "adjustability"],
        },
    ),
    _scenario(
        scenario_id="espresso-machine",
        title="Espresso machine with easy cleanup",
        query="espresso machine",
        budget=700,
        criteria=[
            _criterion("easy cleaning", "must_have", 1.5),
            _criterion("consistent milk steaming", "preference", 1.0),
            _criterion("small kitchen footprint", "preference", 1.0),
            _criterion("pods only", "avoid", 1.0),
        ],
        expectations={
            "min_recommended_source_count": 2,
            "required_verification_status": "verified",
            "required_criterion_names": ["easy cleaning", "consistent milk steaming"],
            "forbidden_recommended_name_terms": ["pod", "capsule"],
        },
    ),
    _scenario(
        scenario_id="mechanical-keyboard",
        title="Mechanical keyboard for quiet office use",
        query="mechanical keyboard",
        budget=180,
        criteria=[
            _criterion("quiet typing", "must_have", 1.5),
            _criterion("wireless connectivity", "preference", 1.0),
            _criterion("tenkeyless or compact layout", "preference", 1.0),
            _criterion("clicky switches", "avoid", 1.2),
        ],
        notes="Avoid boards that will be too loud in a shared office.",
        expectations={
            "min_recommended_source_count": 2,
            "required_verification_status": "verified",
            "required_criterion_names": ["quiet typing", "wireless connectivity"],
            "forbidden_recommended_name_terms": ["clicky"],
        },
    ),
    _scenario(
        scenario_id="4k-monitor",
        title="4K monitor for productivity",
        query="4K monitor",
        budget=500,
        criteria=[
            _criterion("sharp text clarity", "must_have", 1.5),
            _criterion("USB-C connectivity", "preference", 1.0),
            _criterion("adjustable stand", "preference", 1.0),
            _criterion("limited warranty", "avoid", 1.0),
        ],
        expectations={
            "min_recommended_source_count": 2,
            "required_verification_status": "verified",
            "required_criterion_names": ["sharp text clarity", "USB-C connectivity", "adjustable stand"],
        },
    ),
    _scenario(
        scenario_id="standing-desk",
        title="Standing desk for small home office",
        query="standing desk",
        budget=600,
        criteria=[
            _criterion("stability at standing height", "must_have", 1.5),
            _criterion("desktop size for dual monitors", "preference", 1.0),
            _criterion("quiet motor", "preference", 1.0),
            _criterion("manual crank design", "avoid", 1.0),
        ],
        expectations={
            "min_recommended_source_count": 2,
            "required_verification_status": "verified",
            "required_criterion_names": ["stability at standing height", "quiet motor"],
        },
    ),
    _scenario(
        scenario_id="carry-on-luggage",
        title="Carry-on luggage for domestic flights",
        query="carry-on suitcase",
        budget=250,
        criteria=[
            _criterion("fits common US airline carry-on limits", "must_have", 1.5),
            _criterion("durability", "preference", 1.0),
            _criterion("smooth wheels", "preference", 1.0),
            _criterion("checked-bag-only size", "avoid", 1.2),
        ],
        expectations={
            "min_recommended_source_count": 2,
            "required_verification_status": "verified",
            "required_criterion_names": ["fits common US airline carry-on limits", "durability"],
            "forbidden_recommended_name_terms": ["28-inch", "29-inch"],
        },
    ),
    _scenario(
        scenario_id="air-purifier",
        title="Air purifier for bedroom use",
        query="air purifier",
        budget=250,
        criteria=[
            _criterion("quiet sleep mode", "must_have", 1.5),
            _criterion("strong filtration for smoke or dust", "preference", 1.0),
            _criterion("reasonable replacement filter cost", "preference", 1.0),
            _criterion("excessively loud operation", "avoid", 1.0),
        ],
        expectations={
            "min_recommended_source_count": 2,
            "required_verification_status": "verified",
            "required_criterion_names": ["quiet sleep mode", "strong filtration for smoke or dust"],
        },
    ),
    _scenario(
        scenario_id="robot-vacuum",
        title="Robot vacuum for pet hair",
        query="robot vacuum",
        budget=500,
        criteria=[
            _criterion("pet hair pickup", "must_have", 1.5),
            _criterion("reliable navigation", "preference", 1.0),
            _criterion("easy maintenance", "preference", 1.0),
            _criterion("poor app support", "avoid", 1.0),
        ],
        expectations={
            "min_recommended_source_count": 2,
            "required_verification_status": "verified",
            "required_criterion_names": ["pet hair pickup", "reliable navigation"],
        },
    ),
    _scenario(
        scenario_id="electric-toothbrush",
        title="Electric toothbrush with value focus",
        query="electric toothbrush",
        budget=120,
        criteria=[
            _criterion("gentle cleaning", "must_have", 1.5),
            _criterion("replacement brush head availability", "preference", 1.0),
            _criterion("battery life", "preference", 1.0),
            _criterion("subscription-only features", "avoid", 1.0),
        ],
        expectations={
            "min_recommended_source_count": 2,
            "required_verification_status": "verified",
            "required_criterion_names": ["gentle cleaning", "battery life"],
        },
    ),
    _scenario(
        scenario_id="webcam",
        title="Webcam for remote meetings",
        query="webcam",
        budget=150,
        criteria=[
            _criterion("sharp image in indoor lighting", "must_have", 1.5),
            _criterion("plug-and-play setup", "preference", 1.0),
            _criterion("good microphone quality", "preference", 1.0),
            _criterion("requires special proprietary dock", "avoid", 1.0),
        ],
        expectations={
            "min_recommended_source_count": 2,
            "required_verification_status": "verified",
            "required_criterion_names": ["sharp image in indoor lighting", "plug-and-play setup"],
        },
    ),
    _scenario(
        scenario_id="hiking-backpack",
        title="Day-hiking backpack with hydration support",
        query="hiking backpack",
        budget=180,
        criteria=[
            _criterion("comfortable fit for day hikes", "must_have", 1.5),
            _criterion("hydration compatibility", "preference", 1.0),
            _criterion("weather resistance", "preference", 1.0),
            _criterion("ultralight but fragile construction", "avoid", 1.0),
        ],
        allowed_domains=["rei.com", "backcountry.com"],
        expectations={
            "min_recommended_source_count": 1,
            "required_verification_status": "verified",
            "required_criterion_names": ["comfortable fit for day hikes", "hydration compatibility"],
            "require_recommended_url_in_allowed_domains": True,
        },
    ),
    _scenario(
        scenario_id="blender",
        title="Blender for smoothies and frozen fruit",
        query="blender",
        budget=250,
        criteria=[
            _criterion("handles frozen fruit well", "must_have", 1.5),
            _criterion("easy cleaning", "preference", 1.0),
            _criterion("countertop footprint", "preference", 1.0),
            _criterion("weak motor", "avoid", 1.0),
        ],
        expectations={
            "min_recommended_source_count": 2,
            "required_verification_status": "verified",
            "required_criterion_names": ["handles frozen fruit well", "easy cleaning"],
        },
    ),
    _scenario(
        scenario_id="running-shoes-neutral",
        title="Neutral running shoes for daily training",
        query="running shoes",
        budget=170,
        criteria=[
            _criterion("daily training comfort", "must_have", 1.5),
            _criterion("durability", "preference", 1.0),
            _criterion("breathability", "preference", 1.0),
            _criterion("carbon racing plate", "avoid", 1.0),
        ],
        notes="Need a neutral daily trainer, not a race-day shoe.",
        expectations={
            "min_recommended_source_count": 2,
            "required_verification_status": "verified",
            "required_criterion_names": ["daily training comfort", "durability"],
            "forbidden_recommended_name_terms": ["carbon", "race"],
        },
    ),
]
