from app.models import Outlet


def fallback_local_graf(outlet: Outlet, headline: str) -> str:
    town = outlet.town or outlet.name
    return (
        f"In {town}, the story lands on a different street map: councillors, traders and "
        f"residents will judge it by what changes on the ground here, not by a national average. "
        f"Local reporters should still add a named voice and a place-specific fact before this "
        f"graf is treated as finished copy for “{headline}”."
    )


def compose_variant(spine_body: str, local_graf: str, outlet: Outlet) -> str:
    """Shared spine + one local graf. Deliberately not synonym spinning."""
    graf = (local_graf or "").strip() or fallback_local_graf(outlet, outlet.name)
    return f"{spine_body.rstrip()}\n\n{graf}\n"
