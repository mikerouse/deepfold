from app.enums import JobKind, JobStatus
from app.models import Draft, Job
from app.services.worker_status import worker_labels, worker_status


def test_queued_and_claimed_labels():
    draft = Draft(headline="Test", spine_body="", status="drafting")
    draft.jobs = [
        Job(kind=JobKind.draft_article.value, status=JobStatus.queued.value),
        Job(kind=JobKind.featured_image.value, status=JobStatus.queued.value),
    ]
    assert worker_status(draft) == "Queued for drafting"
    assert worker_labels(draft) == ["Queued for drafting", "Queued for image"]

    draft.jobs[0].status = JobStatus.claimed.value
    assert worker_status(draft) == "Drafting…"
    draft.jobs[0].status = JobStatus.completed.value
    draft.jobs[1].status = JobStatus.claimed.value
    assert worker_status(draft) == "Generating image…"


def test_ready_for_check_only_when_asked():
    draft = Draft(headline="Test", spine_body="Body copy here.", status="drafting")
    draft.jobs = [Job(kind=JobKind.draft_article.value, status=JobStatus.completed.value)]
    assert worker_status(draft) is None
    assert worker_status(draft, include_ready=True) == "Ready for check"
