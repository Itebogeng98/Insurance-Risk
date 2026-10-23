from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.conf import settings
from xml.sax.saxutils import escape
from io import BytesIO

from accounts.audit import write_audit_log
from accounts.models import AuditLog
from applicants.permissions import get_visible_applicant_or_404
from risk_engine.recommendations import build_lifestyle_recommendations


def _report_context(request: HttpRequest, applicant_id: int, assessment_id: int | None = None) -> dict:
    applicant = get_visible_applicant_or_404(
        request.user,
        pk=applicant_id,
    )
    applicant = (
        applicant.__class__.objects.select_related(
            'created_by',
            'medical_history',
            'lifestyle_habits',
            'salary',
            'vehicle_insurance_history',
            'spending_behaviour',
        )
        .prefetch_related('risk_assessments__feature_contributions')
        .prefetch_related('risk_assessments__recommendations')
        .get(pk=applicant.pk)
    )
    latest_assessment = (get_object_or_404(applicant.risk_assessments, pk=assessment_id)
                         if assessment_id is not None else applicant.risk_assessments.first())
    return {
        'applicant': applicant,
        'latest_assessment': latest_assessment,
        'recommendations': (
            [recommendation.message for recommendation in latest_assessment.recommendations.all()]
            if latest_assessment
            else build_lifestyle_recommendations(applicant)
        ),
    }


def _render_pdf(html: str, base_url: str) -> bytes:
    """Render plain report text, escaping any user-provided markup."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [
        Paragraph('Integrated Life Insurance Risk Assessment Report', styles['Title']),
        Spacer(1, 12),
    ]
    for line in html.splitlines():
        stripped = line.strip()
        if stripped:
            story.append(Paragraph(escape(stripped), styles['BodyText']))
            story.append(Spacer(1, 6))
    document.build(story)
    return buffer.getvalue()


@login_required
def underwriting_report(request: HttpRequest, applicant_id: int) -> HttpResponse:
    context = _report_context(request, applicant_id)
    write_audit_log(
        request=request,
        action=AuditLog.Action.DATA_ACCESS,
        object_type='Applicant',
        object_id=applicant_id,
        detail='Underwriting report viewed.',
    )
    return render(
        request,
        'reports/underwriting_report.html',
        context,
    )


@login_required
def underwriting_report_pdf(request: HttpRequest, applicant_id: int) -> HttpResponse:
    context = _report_context(request, applicant_id)
    write_audit_log(
        request=request,
        action=AuditLog.Action.DATA_ACCESS,
        object_type='Applicant',
        object_id=applicant_id,
        detail='Underwriting PDF exported.',
    )
    html = _plain_report_text(context)
    try:
        pdf = _render_pdf(html, request.build_absolute_uri('/'))
    except OSError as exc:
        return HttpResponse(
            f'PDF export is unavailable because the server is missing a PDF system dependency: {exc}',
            status=503,
            content_type='text/plain',
        )
    filename = f'underwriting-report-{context["applicant"].pk}.pdf'
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def _plain_report_text(context: dict) -> str:
    applicant = context['applicant']
    latest = context['latest_assessment']
    lines = [
        'Underwriting Report',
        f'Applicant: {applicant}',
        f'National ID: {applicant.national_id}',
        f'Date of birth: {applicant.date_of_birth}',
        f'Captured by: {applicant.created_by}',
    ]
    if getattr(settings, 'ACADEMIC_DEMO', True):
        lines.insert(0, 'ACADEMIC DEMONSTRATION - experimental output, not an insurance decision.')
    if latest:
        lines.extend([
            f'Risk score: {latest.risk_score}',
            f'Risk category: {latest.risk_category}',
            f'Confidence: {latest.confidence}',
            f'Manual review required: {"Yes" if latest.needs_manual_review else "No"}',
            f'Model version: {latest.model_version}',
            'Rule-based indicators (not model feature attribution):',
        ])
        lines.extend(
            f'{factor.rank}. {factor.label}: {factor.contribution}'
            for factor in latest.feature_contributions.all()
        )
    lines.append('Recommendations:')
    lines.extend(f'- {recommendation}' for recommendation in context['recommendations'])
    return '\n'.join(lines)
