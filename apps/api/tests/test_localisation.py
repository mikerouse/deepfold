from app.models import Outlet
from app.services.localisation import compose_variant


def test_variant_is_spine_plus_local_graf_not_a_rewrite():
    outlet = Outlet(name="Nuneaton Desk", town="Nuneaton", slug="nuneaton-desk")
    spine = "The county will consult in January."
    graf = "In Nuneaton, the Town Hall meeting is the first public date."
    variant = compose_variant(spine, graf, outlet)
    assert variant.startswith(spine)
    assert "In Nuneaton" in variant
    assert "synonym" not in variant.lower()
